# Created by Noah Kantrowitz on 2008-02-19.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
import os
import os.path

from trac.core import *
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import add_script
from trac.config import Option
from trac.util.compat import sorted

from tracforge.admin.model import Project, Prototype
from tracforge.admin.util import locate

class TracForgeAdminModule(Component):
    """A module to manage projects in TracForge."""

    helper_script = Option('tracforge', 'helper_script', default='tracforge-helper',
                           doc='Path to the tracforge-helper script, possibly'
                               'utilizing sudo or similar wrappers.')

    implements(IAdminPanelProvider)    
    
    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRACFORGE_ADMIN'):
            yield ('tracforge', 'TracForge', 'admin', 'Project Admin')
            
    def render_admin_panel(self, req, cat, page, path_info):
        if path_info:
            return self._render_project_view(req, cat, page, path_info)
        
        data = {}
        
        if req.method == 'POST':
            if 'create' in req.args.keys(): # Project creation
                name = req.args.get('shortname', '').strip()
                full_name = req.args.get('fullname', '').strip()
                proto_name = req.args.get('prototype', '').strip()
                if not (name and full_name and proto_name):
                    raise TracError('All arguments are required')
                
                # Make the models
                proto = Prototype(self.env, proto_name)
                if not proto.exists:
                    raise TracError('Penguins on fire')
                
                # Use $PATH on non-Win32
                if os.name == 'nt':
                    spawn = os.spawnv
                else:
                    spawn = os.spawnvp
                
                # Spawn the helper script
                helper = self.helper_script.split()
                helper += [self.env.path, proto_name, name, full_name]
                helper.insert(1, os.path.basename(helper[0]))
                spawn(os.P_NOWAIT, helper.pop(0), helper)
                
                # Redirect to the watcher page
                req.redirect(req.href.admin(cat, page, name))
            elif 'delete' in req.args.keys(): # Project deleteion
                raise TracError, 'Not implemented yet. Sorry.'
        
        data['projects'] = sorted([Project(self.env, n) for n in Project.select(self.env)], key=lambda p: p.name)
        data['prototypes'] = Prototype.select(self.env)
        data['env_base_path'] = os.path.join(os.path.dirname(self.env.path), '')
        
        add_script(req, 'tracforge/js/typewatch1.1.js')
        return 'admin_tracforge_projects.html', data

    def _render_project_view(self, req, cat, page, path_info):
        data = {
            'project': path_info,
            'actions': [],
        }
        action_map = {}
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute('SELECT action, step_direction, args, return FROM tracforge_project_log WHERE project=%s ORDER BY step', (data['project'],))
        for action, step_direction, args, rv in cursor:
            d = {
                'action': action,
                'direction': step_direction,
                'args': args,
                'rv': rv == '1',
                'output': [],
            }
            data['actions'].append(d)
            action_map[action,step_direction] = d
        
        cursor.execute('SELECT ts, action, step_direction, stream, data FROM tracforge_project_output WHERE project=%s ORDER BY ts, stream DESC', (data['project'],))
        for ts, action, step_direction, stream, msg in cursor:
            ts = float(ts)
            output = action_map[action, step_direction]['output']
            if output and abs(output[-1][0] - ts) <= 1e-2 and output[-1][1] == stream:
                output[-1] = (output[-1][0], output[-1][1], output[-1][2]+msg)
            else: 
                output.append((float(ts), stream, msg))
        
        return 'admin_tracforge_project.html', data
