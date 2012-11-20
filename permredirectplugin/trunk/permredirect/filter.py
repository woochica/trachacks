# Created by Noah Kantrowitz on 2007-08-27.
# Copyright (c) 2007-2008 Noah Kantrowitz. All rights reserved.
import sys

from trac.core import *
from trac.config import BoolOption
from trac.web.api import IRequestFilter, RequestDone
from trac.perm import PermissionError
from trac.admin.web_ui import AdminModule

class PermRedirectModule(Component):
    """Redirect users to the login screen on PermissionError."""
    
    implements(IRequestFilter)

    redirect_login_https = BoolOption(
        'permredirect', 'redirect_login_https', 'false',
        """Redirect all requests to /login/ to HTTPS""")

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if not self.redirect_login_https:
            return handler

        path = req.base_path + req.path_info

        pos = req.base_url.find(':')
        base_scheme = req.base_url[:pos]
        base_noscheme = req.base_url[pos:]
        base_noscheme_norm = base_noscheme.rstrip('/')
        if path == req.href.login() and base_scheme == 'http':
            login_url = 'https' + base_noscheme_norm + req.path_info
            if req.query_string:
                login_url = login_url + '?' + req.query_string
            req.redirect(login_url)
        return handler
            
    def post_process_request(self, req, template, data, content_type):    
        if template is None:
            # Some kind of exception in progress
            if req.authname != 'anonymous':
                # Already logged in
                return template, data, content_type
            
            exctype, exc = sys.exc_info()[0:2]

            ref_url = req.base_url + req.path_info
            if req.query_string:
                ref_url = ref_url + "?" + req.query_string
            login_url = req.href.login(referer=ref_url)

            if issubclass(exctype, PermissionError):
                req.redirect(login_url)
            
            try:
                if req.path_info.startswith('/admin') and \
                   not AdminModule(self.env)._get_panels(req)[0]:
                    # No admin panels available, assume user should log in.
                    req.redirect(login_url)
            except RequestDone:
                # Reraise on redirect
                raise
            except Exception:
                # It is possible the error we got called on happened inside
                # the _get_panels call. Be sure to ignore it.
                pass
            
        return template, data, content_type

