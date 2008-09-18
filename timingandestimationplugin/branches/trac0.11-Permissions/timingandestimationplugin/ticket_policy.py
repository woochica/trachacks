from trac.core import *
from trac.perm import PermissionCache, IPermissionRequestor, IPermissionGroupProvider, IPermissionPolicy, PermissionSystem
from trac.ticket.model import Ticket
from trac.config import IntOption, ListOption
from trac.util.compat import set

class InternalTicketsPolicy(Component):
    """Hide internal tickets."""
    implements(IPermissionPolicy)
    
    # IPermissionPolicy(Interface)
    def check_permission(self, action, username, resource, perm):
        self.log.debug("Internal: action:%s, user:%s, resource:%s, perm: %s" %
                       ( action, username, resource, perm))
        self.username = username
        # Look up the resource parentage for a ticket.
        while resource:
            if resource.realm == 'ticket':
                break
            resource = resource.parent
        if resource and resource.realm == 'ticket' and resource.id is not None:
            rtn = self.check_ticket_access(perm, resource)
            self.log.debug("Internal: RESULTS for %s: %s" % (action,rtn))
            return rtn
        return None
    
    # Public methods
    def check_ticket_access(self, perm, res):
        """Return if this req is permitted access to the given ticket ID."""
        try:
            tkt = Ticket(self.env, res.id)
        except TracError:
            return None # Ticket doesn't exist
        private_tkt = tkt.get_value_or_default('internal') == '1'

        if private_tkt:
            # cant just check or we get in an infinite call loop
            perm = PermissionCache(self.env, self.username, None, perm._cache)
            return perm.has_permission(self.config.get('ticket', 'internalgroup', 'TIME_ADMIN' ).upper())
        return None
