# Created by Noah Kantrowitz on 2008-03-11.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.

from trac.config import ListOption, BoolOption
from trac.core import *
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.web.api import IRequestFilter

class SimpleTicketModule(Component):
    """A request filter to implement the SimpleTicket reduced ticket entry form."""
    
    fields = ListOption('simpleticket', 'fields', default='',
                         doc='Fields to hide for the simple ticket entry form.')
    
    show_only = BoolOption('simpleticket', 'show_only', default=False,
                           doc='If True, show only the specified fields rather than hiding the specified fields')

    implements(IRequestFilter, IPermissionRequestor)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
            
    def post_process_request(self, req, template, data, content_type):
        if req.path_info == '/newticket':
            do_filter = 'TICKET_CREATE_SIMPLE' in req.perm and not 'TRAC_ADMIN' in req.perm            
            
            self.log.debug('SimpleTicket: Filtering new ticket form for %s', req.authname)
            if self.show_only:
                data['fields'] = [f for f in data['fields'] if f['name'] in self.fields and f is not None]
            else: 
                data['fields'] = [f for f in data['fields'] if f['name'] not in self.fields and f is not None]

        return template, data, content_type

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TICKET_CREATE_SIMPLE', ['TICKET_CREATE']
