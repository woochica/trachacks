# -*- coding: utf-8 -*-
#
# Copyright 2006 Anton Graham <bladehawke@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#  3. The name of the author may not be used to endorse or promote
#     products derived from this software without specific prior
#     written permission.

# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.auth import IAuthenticator

class AuthRequired(Component):
    """Require anonymous users to authenticate"""
    implements(IRequestFilter) #, IRequestHandler)

    authenticators = ExtensionPoint(IAuthenticator)

    def authenticate(self, req):

        for authenticator in self.authenticators:
            authname = authenticator.authenticate(req)
        if authname:
            return authname
        else:
            return 'anonymous'

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        # OK, we have a bit of a catch 22 here.  Auth info is not available at the
        # point at which filters are invoked, but we need to catch the events for
        # unauthenticated users....
        # So, we need to get the info...
        authname = self.authenticate(req)

        if authname == 'anonymous':
            handler = AuthReqHandler(handler, self)
        return handler

    def post_process_request(self, req, template, content_type):
        return template, content_type

class AuthReqHandler(object):

    def __init__(self, in_handler, filter):
        self.in_handler = in_handler
        self.config = filter.config
        self.log = in_handler.log

    def process_request(self, req):

        if ((req.authname and req.authname is not 'anonymous') or \
            req.path_info.startswith('/login')):
            return self.in_handler.process_request(req)

        self.log.debug('Redirecting to /login:')
        req.redirect(req.href.login())
