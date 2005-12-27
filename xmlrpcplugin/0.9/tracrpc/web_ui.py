from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider
from tracrpc.api import IXMLRPCHandler, XMLRPCSystem
from trac.wiki.formatter import wiki_to_oneliner
import xmlrpclib

class XMLRPCWeb(Component):
    """ Handle XML-RPC calls from HTTP clients, as well as presenting a list of
        methods available to the currently logged in user. Browsing to
        <trac>/RPC2 will display this list. """

    implements(IRequestHandler, ITemplateProvider)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info in ('/login/RPC2', '/RPC2')

    def _send_response(self, req, response):
        req.send_response(200)
        req.send_header('Content-Type', 'text/xml')
        req.send_header('Content-Length', len(response))
        req.end_headers()
        req.write(response)

    def process_request(self, req):
        # Need at least XML_RPC
        req.perm.assert_permission('XML_RPC')

        # Dump RPC functions
        if req.get_header('Content-Type') != 'text/xml':
            namespaces = {}
            for method in XMLRPCSystem(self.env).all_methods(req):
                namespace = method.namespace.replace('.', '_')
                if namespace not in namespaces:
                    namespaces[namespace] = {
                        'description' : wiki_to_oneliner(method.namespace_description, self.env),
                        'methods' : [],
                        'namespace' : method.namespace,
                        }
                namespaces[namespace]['methods'].append((method.signature, wiki_to_oneliner(method.description, self.env), method.permission))
            req.hdf['xmlrpc.functions'] = namespaces
            return 'xmlrpclist.cs', None

        # Handle XML-RPC call
        args, method = xmlrpclib.loads(req.read(int(req.get_header('Content-Length'))))
        try:
            result = XMLRPCSystem(self.env).get_method(method)(req, args)
            self._send_response(req, xmlrpclib.dumps(result, methodresponse=True))
        except xmlrpclib.Fault, e:
            self._send_response(req, xmlrpclib.dumps(e))
        except Exception, e:
            self.log.error(e)
            import traceback
            from StringIO import StringIO
            out = StringIO()
            traceback.print_exc(file = out)
            self.log.error(out.getvalue())
            self._send_response(req, xmlrpclib.dumps(xmlrpclib.Fault(2, "'%s' while executing '%s()'" % (str(e), method))))

    # ITemplateProvider
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
