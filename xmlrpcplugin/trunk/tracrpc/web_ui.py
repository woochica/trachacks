# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import re
import xmlrpclib
import datetime
import base64
from StringIO import StringIO
from pkg_resources import resource_filename
from types import GeneratorType

import genshi

from trac.core import *
from trac.perm import PermissionError
from trac.util.datefmt import utc
from trac.util.text import to_unicode
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.formatter import wiki_to_oneliner

from tracrpc.api import IXMLRPCHandler, XMLRPCSystem
from tracrpc.util import from_xmlrpc_datetime, to_xmlrpc_datetime
from tracrpc.util import exception_to_unicode

try:
    try:
        import json
    except:
        import simplejson as json

    class TracRpcJSONEncoder(json.JSONEncoder):
        """ Extending the JSON encoder to support some additional types:
        1. datetime.datetime => {'__jsonclass__': ["datetime", "<rfc3339str>"]}
        2. xmlrpclib.Fault => unicode
        3. xmlrpclib.Binary => {'__jsonclass__': ["binary", "<base64str>"]} """

        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                # http://www.ietf.org/rfc/rfc3339.txt
                return {'__jsonclass__': ["datetime",
                                obj.strftime('%Y-%m-%dT%H:%M:%S')]}
            elif isinstance(obj, xmlrpclib.Binary):
                return {'__jsonclass__': ["binary",
                                obj.data.encode("base64")]}
            elif isinstance(obj, xmlrpclib.Fault):
                return to_unicode(obj)
            else:
                return json.JSONEncoder(self, obj)

    class TracRpcJSONDecoder(json.JSONDecoder):
        """ Extending the JSON decoder to support some additional types:
        1. {'__jsonclass__': ["datetime", "<rfc3339str>"]} => datetime.datetime
        2. {'__jsonclass__': ["binary", "<base64str>"]} => xmlrpclib.Binary """

        dt = re.compile(
            '^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,}))?')

        def _normalize(self, obj):
            """ Helper to traverse JSON decoded object for custom types. """
            if isinstance(obj, tuple):
                return tuple(self._normalize(item) for item in obj)
            elif isinstance(obj, list):
                return [self._normalize(item) for item in obj]
            elif isinstance(obj, dict):
                if obj.keys() == ['__jsonclass__']:
                    kind, val = obj['__jsonclass__']
                    if kind == 'datetime':
                        dt = self.dt.match(val)
                        if not dt:
                            raise Exception(
                                    "Invalid datetime string (%s)" % val)
                        dt = tuple([int(i) for i in dt.groups() if i])
                        kw_args = {'tzinfo': utc}
                        return datetime.datetime(*dt, **kw_args)
                    elif kind == 'binary':
                        try:
                            bin = val.decode("base64")
                            return xmlrpclib.Binary(bin)
                        except:
                            raise Exception("Invalid base64 string")
                    else:
                        raise Exception("Unknown __jsonclass__: %s" % kind)
                else:
                    return dict(self._normalize(obj.items()))
            elif isinstance(obj, basestring):
                return to_unicode(obj)
            else:
                return obj

        def decode(self, obj, *args, **kwargs):
            obj = json.JSONDecoder.decode(self, obj, *args, **kwargs)
            return self._normalize(obj)
    
except ImportError:
    json = None

class XMLRPCWeb(Component):
    """ Handle XML-RPC calls from HTTP clients, as well as presenting a list of
        methods available to the currently logged in user. Browsing to
        <trac>/xmlrpc or <trac>/login/xmlrpc will display this list. """

    content_type_re = re.compile(r'(text|application)/(xml|json)')

    implements(IRequestHandler, ITemplateProvider)

    # IRequestHandler methods
    def match_request(self, req):
        if req.path_info in ('/login/xmlrpc', '/xmlrpc'):
            return True
        if req.path_info in ('/login/jsonrpc', '/jsonrpc'):
            return True

    def _send_response(self, req, response, content_type='application/xml'):
        response = to_unicode(response).encode("utf-8")
        req.send_response(200)
        req.send_header('Content-Type', content_type)
        req.send_header('Content-Length', len(response))
        req.end_headers()
        req.write(response)

    def process_request(self, req):

        content_type = req.get_header('Content-Type') or 'text/html'
        if not self.content_type_re.match(content_type):
            # Dump RPC functions
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
                    from StringIO import StringIO
                    import traceback
                    out = StringIO()
                    traceback.print_exc(file=out)
                    raise Exception('%s: %s\n%s' % (method.name, str(e), out.getvalue()))
            add_stylesheet(req, 'common/css/wiki.css')
            return ('xmlrpclist.html', {'xmlrpc': {'functions': namespaces,
                                    'json': json and True or False}}, None)

        # Handle RPC call
        if content_type.startswith('application/json'):
            if json:
                self.process_json_request(req, content_type)
            else:
                self.log.debug("RPC(json) call ignored (not available).")
                self._send_response(req, "Error: JSON-RPC not available.\n",
                                    content_type)
        else:
            self.process_xml_request(req, content_type)

    def process_xml_request(self, req, content_type):
        """ Handles XML-RPC requests """
        args, method = xmlrpclib.loads(req.read(int(req.get_header('Content-Length'))))
        self.log.debug("RPC(xml) call by '%s', method '%s' with args: %s" \
                                    % (req.authname, method, repr(args)))
        args = self._normalize_xml_input(args)
        try:
            req.perm.require('XML_RPC') # Need at least XML_RPC
            result = XMLRPCSystem(self.env).get_method(method)(req, args)
            self.env.log.debug("RPC(xml) '%s' result: %s" % (method, repr(result)))
            result = tuple(self._normalize_xml_output(result))
            self._send_response(req, xmlrpclib.dumps(result, methodresponse=True), content_type)
        except PermissionError, e:
            self._send_response(req, xmlrpclib.dumps(xmlrpclib.Fault(1, to_unicode(e))),
                                    content_type)
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

    def process_json_request(self, req, content_type):
        """ Handles JSON-RPC requests """
        try:
            data = json.load(req, cls=TracRpcJSONDecoder)
        except Exception, e:
            # Abort with exception - no data can be read
            self.log.error("RPC(json) decode error %s" % \
                    exception_to_unicode(e, traceback=True))
            response = json.dumps(self._json_error(e, -32700),
                                    cls=TracRpcJSONEncoder)
            self._send_response(req, response + '\n', content_type)
            return
        self.log.debug("RPC(json) call by '%s': %s" % (req.authname, data))
        args = data.get('params') or []
        r_id = data.get('id', None)
        method = data.get('method', '')
        try:
            req.perm.require('XML_RPC') # Need at least XML_RPC
            if method == 'system.multicall': # Custom multicall
                results = []
                for mc in args:
                    results.append(self._json_call(req, mc.get('method', ''),
                        mc.get('params') or [], mc.get('id') or r_id))
                response = {'result': results, 'error': None, 'id': r_id}
            else:
                response = self._json_call(req, method, args, r_id)
            try: # JSON encoding
                self.log.debug("RPC(json) result: %s" % repr(response))
                response = json.dumps(response, cls=TracRpcJSONEncoder)
            except Exception, e:
                response = json.dumps(self._json_error(e, r_id=r_id),
                                        cls=TracRpcJSONEncoder)
        except PermissionError, e:
            response = json.dumps(self._json_error(e, -32600, r_id=r_id),
                cls=TracRpcJSONEncoder)
        except Exception, e:
            self.log.error("RPC(json) error %s" % exception_to_unicode(e,
                                                    traceback=True))
            response = json.dumps(self._json_error(e), cls=TracRpcJSONEncoder)
        self.log.debug("RPC(json) encoded result: %s" % response)
        self._send_response(req, response + '\n', content_type)

    def _json_call(self, req, method, args, r_id=None):
        """ Call method and create response dictionary. """
        try:
            result = (XMLRPCSystem(self.env).get_method(method)(req, args))[0]
            if isinstance(result, GeneratorType):
                result = list(result)
            return {'result': result, 'error': None, 'id': r_id}
        except Exception, e:
            return self._json_error(e, r_id=r_id)

    def _json_error(self, e, c=-32603, r_id=None):
        """ Makes a response dictionary that is an error. """
        return {'result': None, 'id': r_id, 'error': {
                'name': 'JSONRPCError', 'code': c, 'message': to_unicode(e)}}

    def _normalize_xml_input(self, args):
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
                    arg[key] = self._normalize_xml_input([arg[key]])[0]
                new_args.append(arg)
            elif isinstance(arg, list) or isinstance(arg, tuple):
                new_args.append(self._normalize_xml_input(arg))
            else:
                new_args.append(arg)
        return new_args

    def _normalize_xml_output(self, result):
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
                    res[key] = self._normalize_xml_output([res[key]])[0]
                new_result.append(res)
            elif isinstance(res, list) or isinstance(res, tuple):
                new_result.append(self._normalize_xml_output(res))
            else:
                new_result.append(res)
        return new_result

    # ITemplateProvider
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]
