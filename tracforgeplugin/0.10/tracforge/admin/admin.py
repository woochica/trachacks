from trac.core import *

from webadmin.web_ui import IAdminPageProvider

from model import Project

class TracForgeAdminModule(Component):
    """A module to manage projects in TracForge."""

    implements(IAdminPageProvider)    
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRACFORGE_ADMIN'):
            yield ('tracforge', 'TracForge', 'admin', 'Project Admin')
            
    def process_admin_request(self, req, cat, page, path_info):
        
    
        return 'admin_tracforge.cs', None
             
