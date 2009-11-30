from trac.core import *
from trac.web.api import IRequestHandler
from trac.wiki.model import WikiPage

class RobotsTxtModule(Component):
    """Serve a robots.txt file from Trac."""
    
    implements(IRequestHandler)
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/robots.txt'
        
    def process_request(self, req):
        page = WikiPage(self.env, 'RobotsTxt')
        data = ''
        if page.exists:
            data = page.text
        data = data.replace('{{{', '').replace('}}}', '')
        req.send(data, 'text/plain')
        

