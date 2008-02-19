from trac.core import *
from trac.web.chrome import add_stylesheet

from webadmin.web_ui import IAdminPageProvider

from model import Project, Members

class TracForgeMembershipModule(Component):
    """A module to manage project memberships."""

    implements(IAdminPageProvider)    
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRACFORGE_ADMIN'):
            yield ('tracforge', 'TracForge', 'membership', 'Membership')
            
    def process_admin_request(self, req, cat, page, path_info):
        projects = [Project(self.env, n) for n in Project.select(self.env)]
        
        if req.method == 'POST':
            if 'add' in req.args.keys():
                proj = req.args.get('project')
                user = req.args.get('user')
                role = req.args.get('role')
                if proj not in [p.name for p in projects] and proj != '*':
                    raise TracError, 'Invalid project %s'%proj
                if role not in ('member', 'admin'):
                    raise TracError, 'Invalid role %s'%role
                Members(self.env, proj)[user] = role
                req.redirect(req.href.admin(cat, page))       
        
        projects_data = {}
        for proj in projects:
            projects_data[proj.name] = {
                'members': dict(proj.members.iteritems()),
                'env_path': proj.env_path, # Need some dummy value to ensure that the headings show up
            }
            
        req.hdf['tracforge.projects.*'] = {
            'dummy': 1,
            'members': dict(Members(self.env, '*').iteritems()),
        }
        req.hdf['tracforge.projects'] = projects_data
        
        add_stylesheet(req, 'tracforge/css/admin.css')
        return 'admin_tracforge_memebership.cs', None
             
