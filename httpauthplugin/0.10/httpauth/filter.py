from trac.core import *
from trac.config import ListOption
from trac.web.api import IRequestFilter, RequestDone, IAuthenticator
from trac.web.chrome import INavigationContributor

import base64

from acct_mgr.api import AccountManager

__all__ = ['HTTPAuthFilter']

class HTTPAuthFilter(Component):
    """Request filter and handler to provide HTTP authentication."""
    
    paths = ListOption('httpauth', 'paths', default='/xmlrpc',
                       doc='Paths to force HTTP authentication on.')
    
    implements(IRequestFilter, IAuthenticator)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        for path in self.paths:
            if req.path_info.startswith(path):
                header = req.get_header('Authorization')
                if header is None:
                    self.log.info('HTTPAuthFilter: No authentication data given, returing 403')
                    return self # Run HTTP auth
                else:
                    token = header.split()[1]
                    user, passwd = base64.b64decode(token).split(':', 1)
                    if AccountManager(self.env).check_password(user, passwd):
                        self.log.debug('HTTPAuthFilter: Authentication okay')
                        req.__user = user
                    else:
                        self.log.info('HTTPAuthFilter: Bad authentication data given, returing 403')
                        return self # Failed auth
        
        return handler
        
    def post_process_request(self, req, template, content_type):
        return template, content_type

    # IRequestHandler methods        
    def process_request(self, req):
        if req.session:
            req.session.save() # Just in case
        
        req.send_response(401)
        req.send_header('WWW-Authenticate', 'Basic realm="Control Panel"')
        req.send_header('Content-Type', 'text/plain')
        req.send_header('Pragma', 'no-cache')
        req.send_header('Cache-control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.end_headers()
        
        if req.method != 'HEAD':
            req.write('Authentication required')
        raise RequestDone

    # IAuthenticator methods
    def authenticate(self, req):
        try:
            return req.__user
        except AttributeError:
            return None # Bail out
