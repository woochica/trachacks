# Created by Noah Kantrowitz on 2008-03-11.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.

from trac.core import *
from trac.web import IRequestFilter
from trac.perm import IPermissionRequestor
from trac.config import ListOption, BoolOption

class SimpleTicketModule(Component):
    """A request filter to implement the SimpleTicket reduced ticket entry form."""
    
    hide_fields = ListOption('simpleticket', 'hide', default='',
                             doc='What fields to hide for the simple ticket entry form.')
    
    allow_override = BoolOption('simpleticket', 'allow_override', default=False,
                              doc='Allow the user to use the normal entry form even if they have TICKET_CREATE_SIMPLE')

    implements(IRequestFilter, IPermissionRequestor)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
            
    def post_process_request(self, req, template, data, content_type):
        if req.path_info == '/newticket':
            do_filter = req.perm.has_permission('TICKET_CREATE_SIMPLE')
            
            # Should we allow a session override?
            allow_override = self.allow_override or req.perm.has_permission('TRAC_ADMIN')
            if allow_override:
                do_filter = req.session.get('simpleticket.do_filter', do_filter)
            
            if do_filter:
                #self.env.log.info(data)
                for f in self.hide_fields:
                    if data.has_key('fields'):
                        for dict in data['fields']:
                            if (dict['name'] == f ):
#                                self.env.log.info(dict['name'])
                                dict['skip'] = True
                            dict['rendered'] = 'no'

        return template, data, content_type

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TICKET_CREATE_SIMPLE', ['TICKET_CREATE']

