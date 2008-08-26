# Created by Noah Kantrowitz on 2007-08-27.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
import sys
import inspect

from trac.core import *
from trac.web.api import IRequestFilter, RequestDone
from trac.perm import PermissionError

class PermRedirectModule(Component):
    """Redirect users to the login screen on PermissionError."""

    implements(IRequestFilter)
    
    def __init__(self):
        old_exc_info = sys.exc_info
        def new_exc_info():
            return list(old_exc_info())
        sys.exc_info = new_exc_info
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
            
    def post_process_request(self, req, template, content_type):
        if template is None:
            # Some kind of exception in progress
            exctype, exc = sys.exc_info()[0:2]
            if exc is None or exctype is None:
                return template, content_type
            if req.authname == 'anonymous' and \
               (issubclass(exctype, PermissionError) or \
                (issubclass(exctype, TracError) and \
                 exc.message == 'No admin pages available')):
                # Do our redirect
                try:
                    req.redirect(req.href.login())
                except RequestDone:
                    pass # Mask the raise from here, we need to do it later
                
                for frame in inspect.stack()[1:]:
                    l = frame[0].f_locals
                    co = frame[0].f_code
                    if 'err' in l and co.co_name == 'dispatch':
                        # Hijack err
                        err = l['err']
                        err[0] = RequestDone
                        err[1] = None
                        err[2] = None
                        break
            
        return template, content_type


