from trac.core import *
from trac.web.api import IRequestFilter

class NoAnonymousModule(Component):
    """Redirect all anonymous users to the login screen"""
    
    implements(IRequestFilter)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        paths = ['/login', '/reset_password']

        if req.authname == 'anonymous':
            for p in paths:
                if req.path_info.startswith(p):
                    return handler
                    
            # Anonymous user redirect to log in.
            req.redirect(req.href.login())
            # The request above raises RequestDone exception, so we
            # do not have to bother what happens below

        return handler
            
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type
        