from trac.core import *
from trac.web.chrome import ITemplateProvider
from pkg_resources import resource_filename
from trac.web.main import IRequestHandler
from trac.web.chrome import add_stylesheet, add_script
from tracrpc.api import XMLRPCSystem
from trac.perm import IPermissionRequestor
from trac.wiki.formatter import wiki_to_oneliner


class ProcedureList(Component):
    implements(ITemplateProvider, IPermissionRequestor, IRequestHandler)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'RPC_VIEW'

    # ITemplateProvider
    def get_htdocs_dirs(self):
        return [('tracrpc', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/rpc'

    def process_request(self, req):
        req.perm.assert_permission('RPC_VIEW')

        namespaces = {}

        for method in XMLRPCSystem(self.env).all_methods(req):
            namespace = method.namespace.replace('.', '_')
            if namespace not in namespaces:
                namespaces[namespace] = {
                    'description' :
                        wiki_to_oneliner(method.namespace_description, self.env),
                    'methods' : [],
                    'namespace' : method.namespace,
                    }
            try:
                namespaces[namespace]['methods'].append((method.signature,
                    wiki_to_oneliner(method.description, self.env),
                    method.permission))
            except Exception, e:
                from StringIO import StringIO
                import traceback
                out = StringIO()
                traceback.print_exc(file=out)
                raise Exception('%s: %s\n%s' % (method.name, str(e),
                                                out.getvalue()))

        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'tracrpc/css/rpc.css')
        add_script(req, 'tracrpc/js/jquery.js')
        add_script(req, 'tracrpc/js/json.js')
        add_script(req, 'tracrpc/js/jsonrpc.js')
        req.hdf['xmlrpc.functions'] = namespaces
        return 'xmlrpclist.cs', None
