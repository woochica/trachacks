# TracForge prototype admin panel
import itertools

from trac.core import *
from trac.web.chrome import add_stylesheet, add_script
from trac.admin.web_ui import IAdminPanelProvider

from tracforge.admin.model import Prototype, ConfigSet
from tracforge.admin.api import IProjectSetupParticipant, TracForgeAdminSystem

class TracForgePrototypesAdminModule(Component):
    """Configuration screen for TracForge new project settings."""

    #setup_participants = ExtensionPoint(IProjectSetupParticipant)

    implements(IAdminPanelProvider)
    
    def get_admin_panels(self, req):
        if 'TRACFORGE_ADMIN' in req.perm:
            yield 'tracforge', 'TracForge', 'prototypes', 'Project Prototypes'
            yield 'tracforge', 'TracForge', 'configset', 'Configset Management'
            
    def render_admin_panel(self, req, cat, page, path_info):
        data = {}
        
        # General stuff
        add_stylesheet(req, 'tracforge/css/admin.css')

        # Subpage dispatchers
        if path_info:
            if path_info == 'new':
                return self._show_prototype(req, path_info, action='new')
            else:
                return self._show_prototype(req, path_info, action='edit')
        
        data['prototypes'] = Prototype.select(self.env)
        return 'admin_tracforge_prototypes.html', data
        
    def process_configset_admin_request(self, req, cat, page, path_info):
        tags = ['*'] + list(ConfigSet.select(self.env))
        configs = {}
        for t in tags:
            config = ConfigSet(self.env, tag=t, with_star=False)
            configs[t] = dict([(s,config.get(s, with_action=True)) for s in config.sections()])

        if req.method == 'POST':
            if req.args.get('add'):
                # Grab inputs
                tag = req.args.get('tag')
                section = req.args.get('section')
                key = req.args.get('key')
                value = req.args.get('value')
                action = req.args.get('action')
            
                # Input validation
                if not (tag and section and key and action):
                    raise TracError('Not all values given')
                if action not in ('add', 'del'):
                    raise TracError('Invalid action %s'%action)
                if '/' in tag or '/' in section or '/' in key:
                    raise TracError("You cannot use '/' in a tag, section, or key")
            
                config = ConfigSet(self.env, tag=tag, with_star=False)
                config.set(section, key, value, action)
                config.save()
            elif req.args.get('delete'):
                rows = {}
                for row in req.args.getlist('rows'):
                    t,s,k = row.split('/')
                    rows.setdefault(t,[]).append((s,k))
                for t,x in rows.iteritems():
                    config = ConfigSet(self.env, tag=t, with_star=False)
                    for s,k in x:
                        config.remove(s,k)
                    config.save()
            
            req.redirect(req.href.admin(cat, page, path_info))

        req.hdf['tracforge.tags'] = tags            
        #for t in tags: # Force ordering so * is first
        #    req.hdf['tracforge.tags.'+t] = configs[t]
        req.hdf['tracforge.configs'] = configs

        return 'admin_tracforge_configset.cs', None       

    def _show_prototype(self, req, path_info, action):
        """Handler for creating a new prototype."""
        data = {
            'name': path_info,
            'action': action,
        }
        
        proto = None
        if req.method == 'POST':
            proto = Prototype(self.env, '')
            
            for i in itertools.count():
                a = req.args.get('step-%s'%i)
                if a is not None:
                    proto.append((a, req.args['args-%s'%a]))
                else:
                    break
            
            if 'movedown' in req.args:
                i = int(req.args['movedown'])
                x = proto.pop(i)
                proto.insert(i+1, x)
            elif 'moveup' in req.args:
                i = int(req.args['moveup'])
                x = proto.pop(i)
                proto.insert(i-1, x)
            elif 'remove' in req.args:
                i = int(req.args['remove'])
                del proto[i]
            elif 'add' in req.args:
                proto.append((req.args['type'], ''))
            elif 'save' in req.args:
                proto.save()
                req.redirect(req.href.admin('tracforge/prototypes', proto.tag))
            elif 'cancel' in req.args:
                req.redirect(req.href.admin('tracforge/prototypes'))
            elif 'delete' in req.args:
                proto.tag = data['name']
                proto.delete()
                req.redirect(req.href.admin('tracforge/prototypes'))
            
            # Try to figure out the name
            if action == 'new':
                proto.tag = req.args['name']
            else:
                proto.tag = '(modified) %s'%data['name']
            
            
        #steps = {}
        #for p in self.setup_participants:
        #    for a in p.get_setup_actions():
        #        steps[a] = {
        #            'provider': p,
        #            'description': p.get_setup_action_description(a),
        #        }
        data['steps'] = TracForgeAdminSystem(self.env).get_project_setup_participants()
        
        if action == 'new': # For a new one, use the specified defaults 
            if proto is None:
                proto = Prototype.default(self.env) # XXX: This should really read from trac.ini somehow
        elif action == 'edit': 
            if proto is None:
                proto = Prototype(self.env, data['name'])
                if not proto.exists:
                    raise TracError('Unknown prototype %s'%proto.tag)
        else:
            raise TracError('Invalid action %s'%action)
        data['proto'] = proto
        
        add_stylesheet(req, 'tracforge/css/prototypes_new.css')
        #add_script(req, 'tracforge/js/interface/iutil.js')
        #add_script(req, 'tracforge/js/jquery.animatedswap.js')
        return 'admin_tracforge_prototype.html', data
