import re
import xmlrpclib
import datetime
from pkg_resources import resource_filename

import genshi

from trac.core import *
from trac.util.text import to_unicode
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.formatter import wiki_to_oneliner

from tracrpc.api import IXMLRPCHandler, XMLRPCSystem
from tracrpc.util import from_xmlrpc_datetime, to_xmlrpc_datetime

class XMLRPCWeb(Component):
    """ Handle XML-RPC calls from HTTP clients, as well as presenting a list of
        methods available to the currently logged in user. Browsing to
        <trac>/xmlrpc or <trac>/login/xmlrpc will display this list. """

    content_type_re = re.compile(r'(text|application)/xml')

    implements(IRequestHandler, ITemplateProvider)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info in ('/login/xmlrpc', '/xmlrpc')

    def _send_response(self, req, response, content_type='application/xml'):
        req.send_response(200)
        req.send_header('Content-Type', content_type)
        req.send_header('Content-Length', len(response))
        req.end_headers()
        req.write(response)

    def process_request(self, req):
        # Need at least XML_RPC
        req.perm.assert_permission('XML_RPC')

        # Dump RPC functions
        content_type = req.get_header('Content-Type') or 'text/html'
        if not self.content_type_re.match(content_type):
            namespaces = {}
            for method in XMLRPCSystem(self.env).all_methods(req):
                namespace = method.namespace.replace('.', '_')
                if namespace not in namespaces:
                    namespaces[namespace] = {
                        'description' : wiki_to_oneliner(method.namespace_description, self.env),
                        'methods' : [],
                        'namespace' : method.namespace,
                        }
                try:
                    namespaces[namespace]['methods'].append((method.signature, wiki_to_oneliner(method.description, self.env), method.permission))
                except Exception, e:
                    from StringIO import StringIO
                    import traceback
                    out = StringIO()
                    traceback.print_exc(file=out)
                    raise Exception('%s: %s\n%s' % (method.name, str(e), out.getvalue()))
            add_stylesheet(req, 'common/css/wiki.css')
            return ('xmlrpclist.html', {'xmlrpc': {'functions': namespaces}}, None)

        # Handle XML-RPC call
        args, method = xmlrpclib.loads(req.read(int(req.get_header('Content-Length'))))
        self.env.log.debug("RPC(xml) call by '%s', method '%s' with args: %s" \
                                    % (req.authname, method, repr(args)))
        args = self._normalize_input(args)
        try:
            result = XMLRPCSystem(self.env).get_method(method)(req, args)
            self.env.log.debug("RPC(xml) '%s' result: %s" % (method, repr(result)))
            result = tuple(self._normalize_output(result))
            self._send_response(req, xmlrpclib.dumps(result, methodresponse=True), content_type)
        except xmlrpclib.Fault, e:
            self.log.error(e)
            self._send_response(req, xmlrpclib.dumps(e), content_type)
        except Exception, e:
            self.log.error(e)
            import traceback
            from StringIO import StringIO
            out = StringIO()
            traceback.print_exc(file = out)
            self.log.error(out.getvalue())
            self._send_response(req, xmlrpclib.dumps(xmlrpclib.Fault(2, "'%s' while executing '%s()'" % (str(e), method))))

    def _normalize_input(self, args):
        """ Normalizes arguments (at any level - traversing dicts and lists):
        1. xmlrpc.DateTime is converted to Python datetime
        2. String line-endings same as from web (`\n` => `\r\n`)
        """
        new_args = []
        for arg in args:
            # self.env.log.debug("arg %s, type %s" % (arg, type(arg)))
            if isinstance(arg, xmlrpclib.DateTime):
                new_args.append(from_xmlrpc_datetime(arg))
            elif isinstance(arg, basestring):
                new_args.append(arg.replace("\n", "\r\n"))
            elif isinstance(arg, dict):
                for key in arg.keys():
                    arg[key] = self._normalize_input([arg[key]])[0]
                new_args.append(arg)
            elif isinstance(arg, list) or isinstance(arg, tuple):
                new_args.append(self._normalize_input(arg))
            else:
                new_args.append(arg)
        return new_args

    def _normalize_output(self, result):
        """ Normalizes and converts output (traversing it):
        1. None => ''
        2. datetime => xmlrpclib.DateTime
        3. genshi.builder.Fragment|genshi.core.Markup => unicode
        """
        new_result = []
        for res in result:
            if isinstance(res, datetime.datetime):
                new_result.append(to_xmlrpc_datetime(res))
            elif res == None:
                new_result.append('')
            elif isinstance(res, genshi.builder.Fragment) \
                        or isinstance(res, genshi.core.Markup):
                new_result.append(to_unicode(res))
            elif isinstance(res, dict):
                for key in res.keys():
                    res[key] = self._normalize_output([res[key]])[0]
                new_result.append(res)
            elif isinstance(res, list) or isinstance(res, tuple):
                new_result.append(self._normalize_output(res))
            else:
                new_result.append(res)
        return new_result

    # ITemplateProvider
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]
