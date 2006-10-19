# TracForge Config Set admin panel
from trac.core import *

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
            configs[t] = dict([(s,config.get(s)) for s in config.sections()])

        if req.method == 'POST':
            req.redirect(req.href.admin(cat, page, path_info))
            
        for t in tags: # Force ordering so * is first
            req.hdf['tracforge.tags.'+t] = configs[t]

        return 'admin_tracforge_configset.cs', None       
