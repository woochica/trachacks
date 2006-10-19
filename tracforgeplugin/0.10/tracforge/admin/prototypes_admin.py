# TracForge Config Set admin panel
from trac.core import *
from trac.web.chrome import add_stylesheet

from webadmin.web_ui import IAdminPageProvider

from model import ConfigSet

class TracForgePrototypesAdminModule(Component):
    """Configuration screen for TracForge new project settings."""

    implements(IAdminPageProvider)
    
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRACFORGE_ADMIN'):
            yield ('tracforge', 'TracForge', 'prototypes', 'Project Prototypes')
            
    def process_admin_request(self, req, cat, page, path_info):
        if path_info and path_info.startswith('config'):
            return TracForgeConfigSetAdminModule(self.env).process_admin_request(req, cat, page, path_info)

        req.hdf['tracforge.href.configset'] = req.href.admin(cat, page, 'config')
        return 'admin_tracforge_prototypes.cs', None
        
class TracForgeConfigSetAdminModule(Component):
    """Configuration screen for TracForge config sets.
    Not reachable directly, but lives at /config under the prototypes screen.
    """
    
    def process_admin_request(self, req, cat, page, path_info):
        tags = ['*'] + list(ConfigSet.select(self.env))
        configs = {}
        for t in tags:
            config = ConfigSet(self.env, tag=t, with_star=False)
            configs[t] = dict([(s,config.get(s, with_action=True)) for s in config.sections()])

        if req.method == 'POST':
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
            
            config = ConfigSet(self.env, tag=tag, with_star=False)
            config.set(section, key, value, action)
            config.save()            
            
            req.redirect(req.href.admin(cat, page, path_info))

        req.hdf['tracforge.tags'] = tags            
        #for t in tags: # Force ordering so * is first
        #    req.hdf['tracforge.tags.'+t] = configs[t]
        req.hdf['tracforge.configs'] = configs

        add_stylesheet(req, 'tracforge/css/admin.css')
        return 'admin_tracforge_configset.cs', None       
