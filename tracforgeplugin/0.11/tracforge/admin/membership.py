# Created by Noah Kantrowitz
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
from trac.core import *
from trac.web.chrome import add_stylesheet
from trac.admin.web_ui import IAdminPanelProvider
from trac.util.compat import sorted
from trac.util.translation import _

from tracforge.admin.model import Project, Members

class TracForgeMembershipModule(Component):
    """A module to manage project memberships."""
    
    implements(IAdminPanelProvider)    
    
    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if 'TRACFORGE_ADMIN' in req.perm:
            yield 'tracforge', _('TracForge'), 'membership', _('Membership')
    
    def render_admin_panel(self, req, cat, page, path_info):
        data = {}
        projects = sorted([(n, Project(self.env, n)) 
                           for n in Project.select(self.env)])
        projects.insert(0, ('*', Project(self.env, '*')))
        
        
        if req.method == 'POST':
            if 'add' in req.args:
                proj = req.args.get('project')
                user = req.args.get('user')
                role = req.args.get('role')
                if proj not in [n for n, p in projects]:
                    raise TracError(_('Invalid project %s'), proj)
                if role not in ('member', 'admin'):
                    raise TracError(_('Invalid role %s'), role)
                Members(self.env, proj)[user] = role
                req.redirect(req.href.admin(cat, page))
            elif 'remove' in req.args:
                db = self.env.get_db_cnx()
                for name, proj in projects:
                    users = req.args.getlist('sel'+name)
                    members = Members(self.env, name, db=db)
                    for user in users:
                        del members[user]
                db.commit()
                req.redirect(req.href.admin(cat, page))
                    
        
        # projects_data = {}
        # for proj in projects:
        #     projects_data[proj.name] = {
        #         'members': dict(proj.members.iteritems()),
        #         'env_path': proj.env_path, # Need some dummy value to ensure that the headings show up
        #     }
        # 
        data['projects'] = projects
            
        # req.hdf['tracforge.projects.*'] = {
        #     'dummy': 1,
        #     'members': dict(Members(self.env, '*').iteritems()),
        # }
        #req.hdf['tracforge.projects'] = projects_data
        
        add_stylesheet(req, 'tracforge/css/admin.css')
        return 'admin_tracforge_membership.html', data
             
