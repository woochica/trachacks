# Created by  on 2008-05-23.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
import re

from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import add_link, add_warning
from trac.config import Option

class OpenIDDelegateFilter(Component):
    """A filter to add OpenID delegate links."""

    implements(IRequestFilter)
    
    server = Option('openid', 'server',
                    doc='Server to use for OpenID delegation.')
    
    delegate = Option('openid', 'delegate',
                      doc='Identity to use for OpenID delegation.')

    known_servers = {
        r'^http://[^.]+.livejournal.com$': 'http://www.livejournal.com/openid/server.bml',
    }
    
    def __init__(self):
        self.known_servers = dict([(re.compile(k, re.U), v) 
                                  for k, v in self.known_servers.iteritems()])

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, mimetype):
        if self.delegate:
            add_link(req, 'openid.delegate', self.delegate)
            server = self.server
            if not server:
                for id_regex, server_href in self.known_servers.iteritems():
                    if id_regex.search(self.delegate):
                        server = server_href
                        break
                else:
                    add_warning(req, 'OpenID for identity %s unknown.',
                                     self.delegate)
                    return template, data, mimetype
            add_link(req, 'openid.server', server)
            
        elif 'TRAC_ADMIN' in req.perm:
            # Warn admins if the plugin is enabled, but not configured
            add_warning(req, 'No OpenID identity specified for delegation.')
        return template, data, mimetype

