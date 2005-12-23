from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider
from tracrpc.api import IXMLRPCHandler, XMLRPCSystem
from trac.wiki.formatter import wiki_to_oneliner
import xmlrpclib
import inspect
import types

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
        # Dump RPC functions
        if req.get_header('Content-Type') != 'text/xml':
            req.hdf['xmlrpc.functions'] = [[x[0]] + [wiki_to_oneliner(x[1], self.env)] for x in XMLRPCSystem(self.env).list_xmlrpc_functions(req)]
            return 'xmlrpclist.cs', None

        # Handle XML-RPC call
        args, procedure = xmlrpclib.loads(req.read(int(req.get_header('Content-Length'))))
        for provider in self.procedures:
            for candidate in provider.get_xmlrpc_functions():
                permission, callable, name, doc = XMLRPCSystem(self.env).resolve_candidate(candidate)
                if name == procedure:
                    req.perm.assert_permission(permission)
                    try:
                        # Pass optional "req" arg if required
                        argspec = inspect.getargspec(callable)[0]
                        if (argspec and argspec[0] == 'req') or (len(argspec) > 1 and argspec[0:2] == ['self', 'req']):
                            result = callable(req, *args)
                        else:
                            result = callable(*args)
                        # If result is null, return an empty tuple
                        if result is None:
                            result = tuple()
                        elif type(result) is types.GeneratorType:
                            result = tuple(result)
                        else:
                            result = (result,)
                    except Exception, e:
                        self.log.error(e)
                        import traceback
                        from StringIO import StringIO
                        out = StringIO()
                        traceback.print_exc(file = out)
                        self.log.error(out.getvalue())
                        req.send_header('Content-Type', 'text/xml')
                        req.end_headers()
                        req.write(xmlrpclib.dumps(xmlrpclib.Fault(e.__class__.__name__, "'%s' while executing '%s()'" % (str(e), procedure))))
                        return None

                    req.send_header('Content-Type', 'text/xml')
                    req.end_headers()
                    req.write('<?xml version="1.0"?>\r\n')
                    req.write(xmlrpclib.dumps(result))
                    return None

        req.send_header('Content-Type', 'text/xml')
        req.end_headers()
        req.write(xmlrpclib.dumps(xmlrpclib.Fault("NoSuchFunction", "No such function '%s'" % procedure)))

    # ITemplateProvider
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

