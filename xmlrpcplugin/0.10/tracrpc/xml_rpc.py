from trac.core import *
from trac.web.main import IRequestHandler
from tracrpc.api import XMLRPCSystem
from trac.perm import IPermissionRequestor
import xmlrpclib


class XMLRPCWeb(Component):
    """ Handle XML-RPC calls from HTTP clients, as well as presenting a list of
        methods available to the currently logged in user. Browsing to
        <trac>/xmlrpc will display this list. """

    implements(IRequestHandler, IPermissionRequestor)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'XML_RPC'

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info in ('/login/xmlrpc', '/xmlrpc')

    def _send_response(self, req, response):
        req.send_response(200)
        req.send_header('Content-Type', 'text/xml')
        req.send_header('Content-Length', len(response))
        req.end_headers()
        req.write(response)

    def process_request(self, req):
        # Need at least XML_RPC
        req.perm.assert_permission('XML_RPC')

        args, method = xmlrpclib.loads(req.read(int(req.get_header('Content-Length'))))
        try:
            result = XMLRPCSystem(self.env).get_method(method)(req, args)
            self._send_response(req, xmlrpclib.dumps(result, methodresponse=True))
        except xmlrpclib.Fault, e:
            self.log.error(e)
            self._send_response(req, xmlrpclib.dumps(e))
        except Exception, e:
            self.log.error(e)
            import traceback
            from StringIO import StringIO
            out = StringIO()
            traceback.print_exc(file = out)
            self.log.error(out.getvalue())
            self._send_response(req, xmlrpclib.dumps(xmlrpclib.Fault(2, "'%s' while executing '%s()'" % (str(e), method))))

