from trac.core import *
from model import Project, Prototype
from trac.admin import IAdminPanelProvider

class TracForgeAdminModule(Component):
    """A module to manage projects in TracForge."""

    implements(IAdminPanelProvider)
    
    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRACFORGE_ADMIN'):
            yield ('tracforge', 'TracForge', 'admin', 'Project Admin')

    def process_admin_request(self, req, cat, page, path_info):
        if req.method == 'POST':
            if 'create' in req.args.keys(): # Project creation
                name = req.args.get('shortname', '').strip()
                fullname = req.args.get('fullname', '').strip()
                env_path = req.args.get('env_path', '').strip()
                proto_name = req.args.get('prototype', '').strip()
                if not (name and fullname and env_path and proto_name):
                    raise TracError('All arguments are required')
                
                # Make the models
                proj = Project(self.env, name)
                proto = Prototype(self.env, proto_name)
                if not proto.exists:
                    raise TracError('Penguins on fire')
                
                # Store the project
                proj.env_path = env_path
                proj.save()
                
                # Apply the prototype
                proto.apply(req, proj)
                
                db = self.env.get_db_cnx()
                cursor = db.cursor()
                cursor.execute('SELECT action, args, return, stdout, stderr FROM tracforge_project_log WHERE project=%s ORDER BY id',(proj.name,))
                
                output = []
                for action, args, rv, out, err in cursor:
                    output.append({
                        'action': action,
                        'args': args,
                        'rv': rv,
                        'out': out.splitlines(),
                        'err': err.splitlines(),
                    })
                        
                req.hdf['tracforge.output'] = output
                req.hdf['tracforge.href.projects'] = req.href.admin(cat, page)
                #req.args['hdfdump'] = 1
                return 'admin_tracforge_project_new.cs', None
                req.redirect(req.href.admin(cat, page))
            elif 'delete' in req.args.keys(): # Project deleteion
                raise TracError, 'Not implemented yet. Sorry.'

        #self.log.debug('TracForge: Starting data grab')
        projects = [Project(self.env, n) for n in Project.select(self.env)]
        #self.log.debug('TracForge: Done with data grab')
    
        #self.log.debug('TracForge: Starting data grab')
        project_data = {}
        for proj in projects:
            #self.log.debug('TracForge: Getting data for %s', proj.name)
            project_data[proj.name] = {
                'fullname': proj.valid and proj.env.project_name or '',
                'env_path': proj.env_path,
            }
        #self.log.debug('TracForge: Done with data grab')
            
        req.hdf['tracforge.projects'] = project_data
        req.hdf['tracforge.prototypes'] = Prototype.select(self.env)
    
        return 'admin_tracforge.cs', None
             
