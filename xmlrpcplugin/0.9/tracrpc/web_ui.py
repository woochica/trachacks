from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider
#from trac.web import auth
from tracrpc.api import IXMLRPCProvider, XMLRPCSystem
import xmlrpclib

class XMLRPCWeb(Component):
    implements(IRequestHandler, ITemplateProvider)

    procedures = ExtensionPoint(IXMLRPCProvider)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/RPC2'

    def process_request(self, req):
        # TODO Authentication/authorisation
        if req.method != 'POST' or req.get_header('Content-Type') != 'text/xml':
            req.hdf['xmlrpc.functions'] = functions = XMLRPCSystem(self.env).list_xmlrpc_functions()
            return 'xmlrpclist.cs', None

        # Handle XML-RPC call
        args, procedure = xmlrpclib.loads(req.read(int(req.get_header('Content-Length'))))
        req.send_header('Content-Type', 'text/xml')
        req.end_headers()
        for provider in self.procedures:
            for candidate in provider.get_xmlrpc_functions():
                permission, callable, name, doc = XMLRPCSystem(self.env).resolve_candidate(candidate)
                if name == procedure:
                    try:
                        result = callable(*args)
                        if not result:
                            result = tuple()
                        else:
                            result = tuple(result,)
                    except Exception, e:
                        import traceback
                        from StringIO import StringIO
                        out = StringIO()
                        traceback.print_exc(file = out)
                        self.log.debug(str(e) + '\n' + out.getvalue())
                        req.write(xmlrpclib.dumps(xmlrpclib.Fault(e.__class__.__name__, "'%s' while executing '%s()'" % (str(e), procedure))))
                        return None

                    req.write('<?xml version="1.0"?>\r\n')
                    req.write(xmlrpclib.dumps(result))
                    return None
        req.write(xmlrpclib.dumps(xmlrpclib.Fault("NoSuchFunction", "No such function '%s'" % procedure)))

    # ITemplateProvider
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

