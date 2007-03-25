from trac.core import *
from trac.web.api import HTTPNotFound
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet
from tracrpc.api import IXMLRPCHandler, XMLRPCSystem
from trac.wiki.formatter import wiki_to_oneliner
from trac.perm import IPermissionRequestor
from fnmatch import fnmatch
from tracrpc.api import XMLRPCSystem
import simplejson


class JSONRPCWeb(Component):
    """Handle JSON-RPC calls from clients."""

    implements(IRequestHandler, IPermissionRequestor)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'JSON_RPC'

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info in '/jsonrpc'

    def process_request(self, req):
        req.perm.assert_permission('JSON_RPC')
        self.env.log.debug(req.args)
        callback = req.args.get('jsonp', req.args.get('callback'))
        method = req.args.get('method', '')
        params = req.args.get('params', '')
        args = []
        kwargs = {}
        if params:
            params = simplejson.loads(req.args.get('params', ''))
        id = req.args.get('id')
        result, = XMLRPCSystem(self.env).get_method(method)(req, params)
        result = simplejson.dumps({'id': id, 'result': result, 'error': None})
        self.env.log.debug(type(result))
        if callback:
            self._send_response(req, '%s(%s)' % (callback, result))
        else:
            self.env.log.debug(result)
            self._send_response(req, result)

    # Internal methods
    def _send_response(self, req, response):
        req.send_response(200)
        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(response))
        req.end_headers()
        req.write(response)
