# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import sys
from types import GeneratorType

from pkg_resources import resource_filename

from genshi.builder import tag
from genshi.template.base import TemplateSyntaxError, BadDirectiveError
from genshi.template.text import TextTemplate

from trac.core import *
from trac.perm import PermissionError
from trac.resource import ResourceNotFound
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.web.api import RequestDone, HTTPUnsupportedMediaType, \
                          HTTPInternalError
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor, \
                            add_stylesheet, add_script, add_ctxtnav
from trac.wiki.formatter import wiki_to_oneliner

from tracrpc.api import XMLRPCSystem, IRPCProtocol, ProtocolException, \
                          RPCError, ServiceException
from tracrpc.util import accepts_mimetype

__all__ = ['RPCWeb']

class RPCWeb(Component):
    """ Handle RPC calls from HTTP clients, as well as presenting a list of
        methods available to the currently logged in user. Browsing to
        <trac>/rpc or <trac>/login/rpc will display this list. """

    implements(IRequestHandler, ITemplateProvider, INavigationContributor)

    protocols = ExtensionPoint(IRPCProtocol)

    # IRequestHandler methods

    def match_request(self, req):
        """ Look for available protocols serving at requested path and
            content-type. """
        content_type = req.get_header('Content-Type') or 'text/html'
        must_handle_request = req.path_info in ('/rpc', '/login/rpc')
        for protocol in self.protocols:
            for p_path, p_type in protocol.rpc_match():
                if req.path_info in ['/%s' % p_path, '/login/%s' % p_path]:
                    must_handle_request = True
                    if content_type.startswith(p_type):
                        req.args['protocol'] = protocol
                        return True
        # No protocol call, need to handle for docs or error if handled path
        return must_handle_request

    def process_request(self, req):
        protocol = req.args.get('protocol', None)
        content_type = req.get_header('Content-Type') or 'text/html'
        if protocol:
            # Perform the method call
            self.log.debug("RPC incoming request of content type '%s' " \
                    "dispatched to %s" % (content_type, repr(protocol)))
            self._rpc_process(req, protocol, content_type)
        elif accepts_mimetype(req, 'text/html') \
                    or content_type.startswith('text/html'):
            return self._dump_docs(req)
        else:
            # Attempt at API call gone wrong. Raise a plain-text 415 error
            body = "No protocol matching Content-Type '%s' at path '%s'." % (
                                                content_type, req.path_info)
            self.log.error(body)
            req.send_error(None, template='', content_type='text/plain',
                    status=HTTPUnsupportedMediaType.code, env=None, data=body)

    # Internal methods

    def _dump_docs(self, req):
        self.log.debug("Rendering docs")

        # Dump RPC documentation
        req.perm.require('XML_RPC') # Need at least XML_RPC
        namespaces = {}
        for method in XMLRPCSystem(self.env).all_methods(req):
            namespace = method.namespace.replace('.', '_')
            if namespace not in namespaces:
                namespaces[namespace] = {
                    'description' : wiki_to_oneliner(
                                    method.namespace_description,
                                    self.env, req=req),
                    'methods' : [],
                    'namespace' : method.namespace,
                    }
            try:
                namespaces[namespace]['methods'].append(
                        (method.signature,
                        wiki_to_oneliner(
                            method.description, self.env, req=req),
                        method.permission))
            except Exception, e:
                from tracrpc.util import StringIO
                import traceback
                out = StringIO()
                traceback.print_exc(file=out)
                raise Exception('%s: %s\n%s' % (method.name,
                                                str(e), out.getvalue()))
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'tracrpc/rpc.css')
        add_script(req, 'tracrpc/rpc.js')
        return ('rpc.html', 
                {'rpc': {'functions': namespaces,
                         'protocols': [p.rpc_info() + (list(p.rpc_match()),) \
                                  for p in self.protocols],
                         'version': __import__('tracrpc', ['__version__']).__version__
                        },
                 'expand_docs': self._expand_docs
                 },
                None)

    def _expand_docs(self, docs, ctx):
        try :
            tmpl = TextTemplate(docs)
            return tmpl.generate(**dict(ctx.items())).render()
        except (TemplateSyntaxError, BadDirectiveError), exc:
            self.log.exception("Syntax error rendering protocol documentation")
            return "'''Syntax error:''' [[BR]] %s" % (str(exc),)
        except Exception:
            self.log.exception("Runtime error rendering protocol documentation")
            return "Error rendering protocol documentation. " \
                       "Contact your '''Trac''' administrator for details"

    def _rpc_process(self, req, protocol, content_type):
        """Process incoming RPC request and finalize response."""
        proto_id = protocol.rpc_info()[0]
        rpcreq = req.rpc = {'mimetype': content_type}
        try :
            self.log.debug("RPC(%s) call by '%s'", proto_id, req.authname)
            rpcreq = req.rpc = protocol.parse_rpc_request(req, content_type)
            rpcreq['mimetype'] = content_type

            # Important ! Check after parsing RPC request to add 
            #             protocol-specific fields in response 
            #             (e.g. JSON-RPC response `id`)
            req.perm.require('XML_RPC') # Need at least XML_RPC

            method_name = rpcreq.get('method')
            if method_name is None :
                raise ProtocolException('Missing method name')
            args = rpcreq.get('params') or []
            self.log.debug("RPC(%s) call by '%s' %s", proto_id, \
                                              req.authname, method_name)
            try :
                result = (XMLRPCSystem(self.env).get_method(method_name)(req, args))[0]
                if isinstance(result, GeneratorType):
                    result = list(result)
            except (RPCError, PermissionError, ResourceNotFound), e:
                raise
            except Exception:
                e, tb = sys.exc_info()[-2:]
                raise ServiceException(e), None, tb
            else :
                protocol.send_rpc_result(req, result)
        except RequestDone :
            raise
        except (RPCError, PermissionError, ResourceNotFound), e:
            self.log.exception("RPC(%s) Error", proto_id)
            try :
                protocol.send_rpc_error(req, e)
            except RequestDone :
                raise
            except Exception, e :
                self.log.exception("RPC(%s) Unhandled protocol error", proto_id)
                self._send_unknown_error(req, e)
        except Exception, e :
            self.log.exception("RPC(%s) Unhandled protocol error", proto_id)
            self._send_unknown_error(req, e)

    def _send_unknown_error(self, req, e):
        """Last recourse if protocol cannot handle the RPC request | error"""
        method_name = req.rpc and req.rpc.get('method') or '(undefined)'
        body = "Unhandled protocol error calling '%s': %s" % (
                                        method_name, to_unicode(e))
        req.send_error(None, template='', content_type='text/plain',
                            env=None, data=body, status=HTTPInternalError.code)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        yield ('tracrpc', resource_filename(__name__, 'htdocs'))

    def get_templates_dirs(self):
        yield resource_filename(__name__, 'templates')

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        pass

    def get_navigation_items(self, req):
        if req.perm.has_permission('XML_RPC'):
            yield ('metanav', 'rpc',
                   tag.a('API', href=req.href.rpc(), accesskey=1))

