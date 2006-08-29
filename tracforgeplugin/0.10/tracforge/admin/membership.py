from trac.core import *

from webadmin.web_ui import IAdminPageProvider

class TracForgeMembershipModule(Component):
    """A module to manage project memberships."""

    implements(IAdminPageProvider)    
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRACFORGE_ADMIN'):
            yield ('tracforge', 'TracForge', 'membership', 'Membership')
            
    def process_admin_request(self, req, cat, page, path_info):
        
    
        return 'admin_tracforge_memebership.cs', None
             
