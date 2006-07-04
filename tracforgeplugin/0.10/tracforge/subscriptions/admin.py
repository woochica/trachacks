# TracForge subscription manager
from trac.core import *
from trac.web.chrome import ITemplateProvider
from webadmin.web_ui import IAdminPageProvider

from manager import SubscriptionManager
from util import open_env

class SubscriptionAdmin(Component):
    """Admin GUI for subscriptions."""
    
    implements(IAdminPageProvider, ITemplateProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRACFORGE_ADMIN'):
            yield ('tracforge', 'Tracforge', 'subscriptions', 'Subscriptions')
            
    def process_admin_request(self, req, cat, page, path_info):
    
        mgr = SubscriptionManager(self.env)
        
        types = list(mgr.get_subscribables())
        subscriptions = {}
        for type in types:
            subscriptions[type] = list(mgr.get_subscriptions(type))
                    
        if req.method == 'POST':
            if req.args.get('add'):
                env = req.args.get('env')
                type = req.args.get('type')
                
                assert type in types
                
                # Verify that this looks like an env
                try:
                    open_env(env)
                except IOError:
                    raise TracError, "'%s' is not a valid Trac environment"%env
                
                if env not in subscriptions[type]:
                    mgr.subscribe_to(env, type)
                req.redirect(req.href.admin(cat,page))
        
        req.hdf['tracforge.types'] = types
        req.hdf['tracforge.subscriptions'] = subscriptions
        return 'tracforge_subscriptions_admin.cs', 'text/html'

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return []
