from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider
from tracrpc.api import IXMLRPCHandler, XMLRPCSystem
from trac.wiki.formatter import wiki_to_oneliner
import xmlrpclib

class XMLRPCWeb(Component):
    """ Handle XML-RPC calls from HTTP clients, as well as presenting a list of
        procedures available to the currently logged in user. Browsing to
        <trac>/RPC2 will display this list. """

    implements(IRequestHandler, ITemplateProvider)

    procedures = ExtensionPoint(IXMLRPCHandler)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info in ('/login/RPC2', '/RPC2')

    def process_request(self, req):
        # Need at least XML_RPC
        req.perm.assert_permission('XML_RPC')

        # Dump RPC functions
        if req.get_header('Content-Type') != 'text/xml':
            req.hdf['xmlrpc.functions'] = [[x[0]] + [wiki_to_oneliner(x[1], self.env)] + [x[2]] for x in XMLRPCSystem(self.env).listMethodsDetailed(req)]
            return 'xmlrpclist.cs', None

        # Handle XML-RPC call
        args, procedure = xmlrpclib.loads(req.read(int(req.get_header('Content-Length'))))
        try:
            result = XMLRPCSystem(self.env).get_procedure(procedure)(req, args)

            req.send_header('Content-Type', 'text/xml')
            req.end_headers()
            req.write(xmlrpclib.dumps(result, methodresponse=True))
            return None
        except xmlrpclib.Fault, e:
            req.send_header('Content-Type', 'text/xml')
            req.end_headers()
            req.write(xmlrpclib.dumps(e))
        except Exception, e:
            self.log.error(e)
            import traceback
            from StringIO import StringIO
            out = StringIO()
            traceback.print_exc(file = out)
            self.log.error(out.getvalue())
            req.send_header('Content-Type', 'text/xml')
            req.end_headers()
            req.write(xmlrpclib.dumps(xmlrpclib.Fault(2, "'%s' while executing '%s()'" % (str(e), procedure))))
            return None

    # ITemplateProvider
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
