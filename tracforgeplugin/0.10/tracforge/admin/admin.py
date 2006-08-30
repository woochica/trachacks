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
        projects = [Project(self.env, n) for n in Project.select(self.env)]

        if req.method == 'POST':
            if 'create' in req.args.keys(): # Project creation
                name = req.args.get('shortname')
                fullname = req.args.get('fullname')
                env_path = req.args.get('env_path')
                proj = Project(self.env, name)
                proj.env_path = env_path
                proj.save()
                req.redirect(req.href.admin(cat, page))
            elif 'delete' in req.args.keys(): # Project deleteion
                raise TracError, 'Not implemented yet. Sorry.'
    
        project_data = {}
        for proj in projects:
            project_data[proj.name] = {
                'fullname': proj.env.project_name,
                'env_path': proj.env_path,
            }
            
        req.hdf['tracforge.projects'] = project_data
    
        return 'admin_tracforge.cs', None
             
