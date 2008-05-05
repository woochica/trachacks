# Created by Noah Kantrowitz on 2007-08-27.
# Copyright (c) 2007-2008 Noah Kantrowitz. All rights reserved.
import sys

from trac.core import *
from trac.web.api import IRequestFilter, RequestDone
from trac.perm import PermissionError
from trac.admin.web_ui import AdminModule

class PermRedirectModule(Component):
    """Redirect users to the login screen on PermissionError."""
    
    implements(IRequestFilter)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
            
    def post_process_request(self, req, template, data, content_type):    
        if template is None:
            # Some kind of exception in progress
            if req.authname != 'anonymous':
                # Already logged in
                return template, data, content_type
            
            exctype, exc = sys.exc_info()[0:2]
            if issubclass(exctype, PermissionError):
                req.redirect(req.href.login())
            
            try:
                if req.path_info.startswith('/admin') and \
                   not AdminModule(self.env)._get_panels(req)[0]:
                    # No admin panels available, assume user should log in.
                    req.redirect(req.href.login())
            except RequestDone:
                # Reraise on redirect
                raise
            except Exception:
                # It is possible the error we got called on happened inside
                # the _get_panels call. Be sure to ignore it.
                pass
            
        return template, data, content_type

