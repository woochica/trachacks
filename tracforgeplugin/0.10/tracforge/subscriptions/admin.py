# TracForge subscription manager
from trac.core import *
from trac.web.chrome import ITemplateProvider
from webadmin.web_ui import IAdminPageProvider

from manager import SubscriptionManager

class SubscriptionAdmin(Component):
    """Admin GUI for subscriptions."""
    
    implements(IAdminPageProvider, ITemplateProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRACFORGE_ADMIN'):
            yield ('tracforge', 'Tracforge', 'subscriptions', 'Subscriptions')
            
    def process_admin_request(self, req, cat, page, path_info):
    
        mgr = SubscriptionManager(self.env)
        subscribables = {}
        for type in mgr.get_subscribables():
            subscribables[type] = mgr.get_subscriptions(type)
        
        req.hdf['tracforge.subscriptions'] = subscribables
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
