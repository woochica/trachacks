# Created by Pedro Paixao 9/1/2008
# Copyright (c) 2008 Pedro Paixao. All rights reserved.
import sys

from trac.core import *
from trac.web.api import IRequestFilter, RequestDone
from trac.perm import PermissionError
from trac.admin.web_ui import AdminModule

class NoAnonymousModule(Component):
    """Redirect all anonymous users to the login screen on PermissionError."""
    
    implements(IRequestFilter)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
            
    def post_process_request(self, req, template, data, content_type):
        try:
            if req.authname == 'anonymous' and \
               not req.path_info.startswith('/login'):
                # Anonymous user redirect to log in.
                req.redirect(req.href.login())
        except RequestDone:
            # Reraise on redirect
            raise
        except Exception:
            # It is possible the error we got called on happened inside
            # the _get_panels call. Be sure to ignore it.
            pass
            
        return template, data, content_type

