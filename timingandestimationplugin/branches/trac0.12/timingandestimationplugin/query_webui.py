from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script

class QueryWebUiAddon(Component):
    implements(IRequestFilter)
                
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'query.html':
            add_script(req, "billing/query.js")
            
        return (template, data, content_type)   
