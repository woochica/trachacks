# -*- coding: utf-8 -*-
#
# Copyright 2010 Stefano Apostolico <s.apostolico@gmail.com>
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
from trac.web import IRequestHandler, IRequestFilter
from trac.config import IntOption, ListOption, Option
from trac.perm import IPermissionRequestor, IPermissionGroupProvider, IPermissionPolicy, PermissionSystem
import sys
import logging
import re

rex_email = re.compile(r"(?:^|\s)[-a-z0-9_.]+@(?:[-a-z0-9]+\.)+[a-z]{2,6}(?:\s|$)",re.IGNORECASE)
                          
def nest( flat, groupby=2, dropodd=True ):
    offset = 0
    ret = []
    while offset < len(flat):
        x = tuple([c for c in flat[offset:offset+groupby]])
        if dropodd and len(x) != groupby:
            break
        offset+=groupby
        ret.append(x)
    return ret

class RuleOption(ListOption):
    def accessor(self, section, name, default):
        cfg =  section.getlist(name, default, ',', True)        
        rules = nest(cfg)
        ret = []
        for rule in rules:
            ret.append((re.compile(rule[0]), rule[1]))
        return ret

class RexListOption(ListOption):
    def accessor(self, section, name, default):
        cfg =  section.getlist(name, default, ',', True)        
        return map(re.compile, cfg)

class RexList(list):
    def __contains__(self, str):
        for rule in self:
            if rule.match(str):                
                return True        
        return False
    
class UrlDefender(Component):
    implements(IRequestFilter, IRequestHandler, IPermissionRequestor, IPermissionPolicy)

    rules = RuleOption('urldefender', 'protect', default=[], doc='')
    login_url = Option('urldefender', 'login_url', default='/login', doc='')
    iii = RexListOption('urldefender', 'ignore', default=('/login', '/reset_password', '/register'), doc='')    

    def __init__(self):
        self.log.debug( self.rules )
        self.ignored_urls = RexList(self.iii)
        self.ignored_urls.append( re.compile(self.login_url) ) # always add login_url
        
    # IPermissionPolicy(Interface)
    def check_permission(self, action, username, resource, perm):
        self.log.debug('check_permission {0}'.format(action, username, resource, perm) )
        return False

    # IPermissionRequestor methods
    def get_permission_actions(self):
        """Return a list of actions defined by this component."""
        self.log.debug('get_permission_actions')
        return []

    def __process(self, req, rule, default_handler):
        self.log.debug('__process %s %s %s' % (req.path_info, rule, default_handler))
        if (req.authname and req.authname == 'anonymous'):
            return self
        return default_handler

    # IRequestFilter methods 
    def pre_process_request(self, req, handler):
        self.log.debug('pre_process_request %s %s' % (req.path_info, handler))
        if req.path_info in self.ignored_urls:
            self.log.debug('ignoring %s' % req.path_info)
            return handler
        
        for rex, rule in self.rules:
            if rex.match(req.path_info):
                self.log.debug('match by %s' % rex.pattern )
                return self.__process( req, rule, handler )
            
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        self.log.debug('post_process_request')
        return template, data, content_type

    # IRequestHandler methods
    def match_request(self, req):
        self.log.debug('666 pre_process_request %s' % req.path_info)
        return False

    def process_request(self, req):
        self.log.debug('pre_process_request %s' % req.path_info)
        req.send_response(301)
        req.send_header('Location', req.base_url + self.login_url)
        req.send_header('Content-Type', 'text/plain')
        req.send_header('Content-Length', 0)
        req.send_header('Pragma', 'no-cache')
        req.send_header('Cache-Control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.end_headers()
