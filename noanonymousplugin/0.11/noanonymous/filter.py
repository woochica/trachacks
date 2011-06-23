"""
Enable it in trac.ini ::

  [components]
  noanonymous.* = enabled

By default static resources from plugins are allowed, i.e URLs
`/chrome/something` are not blocked. If you want to block everything except
`/chrome/common` (standard Trac styles) and `/chrome/site` (environment
customizations), add the following block to `trac.ini` ::

  [noanonymous]
  paranoid = true

"""

from trac.core import *
from trac.web.api import IRequestFilter

class NoAnonymousModule(Component):
    """Redirect all anonymous users to the login screen"""
    
    implements(IRequestFilter)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        paths = ['/login', '/reset_password']
        # #6412 - paranoid mode allows only standard trac static resources
        #         otherwise plugin resources are allowed too (default)
        if self.config.get('noanonymous', 'paranoid', False):
            paths += ['/chrome/site', '/chrome/common']
        else:
            paths += ['/chrome']

        if req.authname == 'anonymous':
            for p in paths:
                if req.path_info.startswith(p):
                    return handler

            # Reconstruct return URL
            if req.path_info.startswith('/logout'):
                returl = None
            else:
                returl = req.base_url + req.path_info
                if req.query_string:
                    returl += '?' + req.query_string

            # Anonymous user redirect to log in.
            req.redirect(req.href.login(referer=returl))
            # The request above raises RequestDone exception, so we
            # do not have to bother what happens below

        return handler
            
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type
        