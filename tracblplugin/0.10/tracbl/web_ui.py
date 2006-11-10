# Web interface for TracBL
from trac.core import *
from trac.web.api import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.util.html import html

class TracBLModule(Component):
    """Main web interface for TracBL."""
    
    implements(IRequestHandler, INavigationContributor, ITemplateProvider)
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/blacklist')
        
    def process_request(self, req):
        req.hdf['tracbl.href'] = {
            'main': req.href.blacklist(),
            'key': req.href.blacklist('key'),
        }
        
        subpage = req.path_info[10:]
        if subpage.startswith('/key'):
            return self._render_key(req)
        
        return 'tracbl.cs', None
        
    def _render_key(self, req):
        if req.method == 'POST':
            if req.args.get('new'):
                req.hdf['tracbl.key.page'] = 'done'
        else:
            req.hdf['tracbl.key.page'] = 'new'
        return 'tracbl_key.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('blacklist', resource_filename(__name__, 'htdocs'))]

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'blacklist'
        
    def get_navigation_items(self, req):
        yield ('mainnav', 'blacklist', html.A('Blacklist', href=req.href.blacklist()))

