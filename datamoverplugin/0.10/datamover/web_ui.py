from trac.core import *
from trac.web.chrome import ITemplateProvider

from webadmin.web_ui import IAdminPageProvider

from api import DatamoverSystem

class DatamoverConfigurationModule(Component):
    """The configuration screen for the datamover plugin."""

    implements(IAdminPageProvider, ITemplateProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('mover', 'Data Mover', 'config', 'Configuration')
    
    def process_admin_request(self, req, cat, page, path_info):
        system = DatamoverSystem(self.env)
        envs = system.all_environments()
        any_mutable = system.any_mutable()
                
        req.hdf['datamover.envs'] = envs
        req.hdf['datamover.any_mutable'] = any_mutable
        return 'datamover_config.cs', None
                
    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        #from pkg_resources import resource_filename
        return []        
