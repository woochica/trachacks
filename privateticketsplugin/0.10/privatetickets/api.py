from trac.core import *
from trac.perm import IPermissionRequestor
from trac.ticket.model import Ticket

__all__ = ['PrivateTicketsSystem']

class PrivateTicketsSystem(Component):
    """Central tasks for the PrivateTickets plugin."""
    
    implements(IPermissionRequestor)
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        actions = ['TICKET_VIEW_REPORTER', 'TICKET_VIEW_ASSIGNED', 'TICKET_VIEW_CC']
        return actions + [('TICKET_VIEW_SELF', actions)]

    # Public methods
    def check_ticket_access(self, req, id):
        """Return if this req is permitted access to the given ticket ID."""
        try:
            tkt = Ticket(self.env, id)
        except TracError:
            return False # Ticket doesn't exist
            
        if req.perm.has_permission('TICKET_VIEW_REPORTER') and \
           tkt['reporter'] == req.authname:
            return True
            
            
        return False
