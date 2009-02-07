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

from trac.core import *
from trac.config import Option
from trac.web.auth import LoginModule

from pycosign import PyCoSign

class CoSignLoginModule(LoginModule):
    """
    A CoSign SSO login module. Based on LoginModule, which implements:
     * IAuthenticator 
     * INavigationContributor
     * IRequestHandler
    """
    
    server = Option('cosign', 'server', doc='Base URL for the CoSign server')
    login_path = Option('cosign', 'login_path', default='/login', 
                        doc='Path component for the login system')
    logout_path = Option('cosign', 'logout_path', default='/logout', 
                        doc='Path component for the logout system')
    service = Option('cosign', 'service', default='',
                        doc='CoSign service name for trac. If login redirect is handled by CoSign filter, do not define this.')
        
    # Internal methods
    def _do_login(self, req):
        if not req.remote_user:
            if not self.service:
                raise Exception("Not define CoSign service name. Login failed.")
            self.cosign.do_login(req)
        super(CoSignLoginModule, self)._do_login(req)

    def _do_logout(self, req):
        if req.authname:
            super(CoSignLoginModule, self)._do_logout(req)
            self.cosign.do_logout(req)
        else:
            req.redirect(req.abs_href())
    
    def cosign(self):
        paths = {
            'server': self.server,
            'service': self.service,
            'login_path': self.login_path,
            'logout_path': self.logout_path,
        }
        return PyCoSign(self.server, **paths)
    cosign = property(cosign)
