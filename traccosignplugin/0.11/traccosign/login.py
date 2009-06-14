# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Jiang Xin <worldhello.net@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Jiang Xin <worldhello.net@gmail.com>

import re

from trac.core import *
from trac.config import Option
from trac.web.auth import LoginModule
from trac.web.api import IRequestHandler
from trac.web import parse_query_string

from pycosign import PyCoSign

class CoSignLoginModule(LoginModule):
    """
    A CoSign SSO login module. Based on LoginModule, which implements:
     * IAuthenticator 
     * INavigationContributor
     * IRequestHandler
    """
    
    hostname = Option('cosign', 'cosign_hostname', doc='Base URL for the CoSign server')
    login_path = Option('cosign', 'cosign_login_path', default='/login', 
                        doc='Path component for the login system')
    logout_path = Option('cosign', 'cosign_logout_path', default='/logout', 
                        doc='Path component for the logout system')
    service = Option('cosign', 'cosign_service', default='',
                        doc='CoSign service name for trac. If login redirect is handled by CoSign filter, do not define this.')

    # IRequestHandler methods

    def match_request(self, req):
        return re.match('/(login|logout)/?$', req.path_info)

    def process_request(self, req):
        if req.path_info.startswith('/login'):
            self._do_login(req)
        elif req.path_info.startswith('/logout'):
            self._do_logout(req)
        self._redirect_back(req)

    # Internal methods
    def _referer_url(self, req):
        """Return Referer URL."""
        referer = req.args.get('referer') or req.get_header('Referer')
        if referer and not (referer == req.base_url or \
                referer.startswith(req.base_url.rstrip('/')+'/')):
            # only redirect to referer if it is from the same site
            referer = None
        return referer
    
    def _redirect_back(self, req):
        """Redirect the user back to the URL she came from."""
        if req.query_string:
            args = parse_query_string(req.query_string)
            referer = args.get('referer')
        else:
            referer = None
        req.redirect(referer or req.abs_href())
    
    def _do_login(self, req):
        if not req.remote_user:
            if not self.service:
                raise Exception("Not define CoSign service name. Login failed.")
            referer = self._referer_url(req)
            self.cosign.do_login(req, referer)
        super(CoSignLoginModule, self)._do_login(req)

    def _do_logout(self, req):
        if req.authname:
            super(CoSignLoginModule, self)._do_logout(req)
        if req.remote_user:
            referer = self._referer_url(req)
            self.cosign.do_logout(req, referer)
    
    def cosign(self):
        paths = {
            'hostname': self.hostname,
            'service': self.service,
            'login_path': self.login_path,
            'logout_path': self.logout_path,
        }
        return PyCoSign(self.hostname, **paths)
    cosign = property(cosign)
