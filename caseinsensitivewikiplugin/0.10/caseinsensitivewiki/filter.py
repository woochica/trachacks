from trac.core import *
from trac.web.api import IRequestFilter
from trac.wiki.model import WikiPage
from trac.wiki.api import WikiSystem

class CaseInsensitiveWikiModule(Component):

    implements(IRequestFilter)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if req.path_info.startswith('/wiki'):
            page_name = req.path_info[6:] or 'WikiStart'
            lower_name = page_name.lower()
            if not WikiPage(self.env, page_name).exists:
                possibles = [p for p in WikiSystem(self.env).get_pages() if lower_name == p.lower()]
                if possibles:
                    req.redirect(req.href.wiki(possibles[0]))
    
        return handler
        
    def post_process_request(self, req, template, content_type):
        return (template, content_type)
