from trac.core import *
from trac.web.api import IRequestFilter
from trac.wiki.model import WikiPage
from trac.wiki.api import WikiSystem

class DelegatedWikiModule(Component):

    implements(IRequestFilter)

    def __init__(self):
        self.redirect_url = self.env.config.get('delegatedwiki', 'redirect_url')
	if self.redirect_url and not self.redirect_url.endswith('/'):
            self.redirect_url = self.redirect_url + '/'
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if self.redirect_url and req.path_info.startswith('/wiki'):
            page_name = req.path_info[6:] or 'WikiStart'
            req.redirect(self.redirect_url + page_name)
        return handler
        
    def post_process_request(self, req, template, content_type):
        return (template, content_type)

