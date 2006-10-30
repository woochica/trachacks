# TracForge Config Set admin panel
from trac.core import *
from trac.web.chrome import add_stylesheet, add_script

from webadmin.web_ui import IAdminPageProvider

from model import Prototype, ConfigSet
from api import IProjectSetupParticipant

class TracForgePrototypesAdminModule(Component):
    """Configuration screen for TracForge new project settings."""

    setup_participants = ExtensionPoint(IProjectSetupParticipant)

    implements(IAdminPageProvider)
    
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRACFORGE_ADMIN'):
            yield ('tracforge', 'TracForge', 'prototypes', 'Project Prototypes')
            
    def process_admin_request(self, req, cat, page, path_info):
        # Page locations
        req.hdf['tracforge.href'] = {
            'prototypes': req.href.admin(cat, page),
            'configset': req.href.admin(cat, page, 'config'),
            'new': req.href.admin(cat, page, 'new'),
            'htdocs': req.href.chrome('tracforge'),
        }
        
        # General stuff
        add_stylesheet(req, 'tracforge/css/admin.css')
        add_script(req, 'tracforge/js/jquery.js')

        # Subpage dispatchers
        if path_info:
            if path_info.startswith('config'):
                return self.process_configset_admin_request(req, cat, page, path_info)
            elif path_info.startswith('new'):
                return self.process_new_admin_request(req, cat, page, path_info)
        
    
        req.hdf['tracforge.prototypes.steps'] = sum([list(p.get_setup_actions()) for p in self.setup_participants], [])
        
        return 'admin_tracforge_prototypes.cs', None
        
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

    def process_new_admin_request(self, req, cat, page, path_info):
        """Handler for creating a new prototype."""
        add_stylesheet(req, 'tracforge/css/prototypes_new.css')
        add_script(req, 'tracforge/js/interface/iutil.js')
        add_script(req, 'tracforge/js/jquery.animatedswap.js')

        steps = {}
        for p in self.setup_participants:
            for a in p.get_setup_actions():
                steps[a] = {
                    'provider': p,
                    'description': p.get_setup_action_description(a),
                }
                
        req.hdf['tracforge.prototypes.steps'] = steps
        
        return 'admin_tracforge_prototypes_new.cs', None
