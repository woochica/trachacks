from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.web.api import IRequestHandler
from trac.wiki.model import WikiPage

__all__ = ['RobotsTxtModule']

class RobotsTxtModule(Component):
    """Serve a robots.txt file from Trac."""
    
    implements(ITemplateProvider, IRequestHandler)
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/robots.txt'
        
    def process_request(self, req):
        page = WikiPage(self.env, 'RobotsTxt')
        data = ''
        if page.exists:
            data = page.text
        req.hdf['robotstxt.data'] = data
        return 'robotstxt.cs', 'text/plain'
        
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        #return [('robotstxt', resource_filename(__name__, 'htdocs'))]
        return []
