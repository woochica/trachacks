from trac.config import Option, ListOption
from trac.core import *
from trac.ticket.api import TicketSystem
from trac.web import IRequestFilter
from utils import wrapfunc

from trac.perm import PermissionSystem, PermissionCache

class RestrictOwnerToList(Component):
    implements(IRequestFilter)
    
    def __init__(self):
        wrapfunc(TicketSystem, "eventually_restrict_owner", eventually_restrict_owner)
        self.env.log.info("RestrictOwnerToList replaced TicketSystem.eventually_restrict_owner")

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

def eventually_restrict_owner(original_callable, self, field, ticket=None):

    field['type'] = 'select'    
    field['options'] = self.env.config.getlist('restrictowners', 'userlist', [])
    field['optional'] = True
