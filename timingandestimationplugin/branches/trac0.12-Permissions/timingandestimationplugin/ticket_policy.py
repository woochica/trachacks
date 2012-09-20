from trac.core import *
from trac.perm import PermissionCache, IPermissionRequestor, IPermissionGroupProvider, IPermissionPolicy, PermissionSystem, DefaultPermissionStore, PermissionError
from trac.ticket.model import Ticket
from trac.config import IntOption, ListOption
from trac.util.compat import set

class InternalTicketsPolicy(Component):
    """Hide internal tickets."""
    implements(IPermissionPolicy)
    group_providers = ExtensionPoint(IPermissionGroupProvider)

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
            rtn = self.check_ticket_access(perm, resource, username)
            self.log.debug("Internal: RESULTS for %s: %s" % (action,rtn))
            return rtn
        return None

    # Internal methods   
    def _get_groups(self, user):
        # Get initial subjects
        groups = set([user])
        for provider in self.group_providers:
            for group in provider.get_permission_groups(user):
                groups.add(group)

        # Essentially the default trac PermissionStore ignores user provided
        # groups so we have to look them up manually: 

        # changed this to only do this for the default permission
        # store this has been reported as broken/very slow for the
        # LDAP permission store
        ps = PermissionSystem(self.env) 
        if isinstance(ps.store, DefaultPermissionStore):
            perms = ps.get_all_permissions()
            repeat = True
            while repeat:
                repeat = False
                for subject, action in perms:
                    if subject in groups and not action.isupper() and action not in groups:
                        groups.add(action)
                        repeat = True 
        
        return groups    

    # Public methods
    def check_ticket_access(self, perm, res, user):
        """Return if this req is permitted access to the given ticket ID."""
        try:
            tkt = Ticket(self.env, res.id)
        except Exception, e:
            self.log.warning("Internal: TandE ticket_policy failed to find a ticket for %s : error: %s" %  (res, unicode(e)))
            return None # Ticket doesn't exist / ticket id was invalid
        private_tkt = tkt['internal'] == '1'

        if private_tkt:
            # cant just check or we get in an infinite call loop
            perm = PermissionCache(self.env, self.username, None, perm._cache)
            groups = self._get_groups(user)
            perm_or_group = self.config.get('ticket', 'internalgroup', 'TIME_ADMIN' )
            it = perm_or_group in groups or perm.has_permission(perm_or_group)
            if not it: raise PermissionError(perm_or_group, res, self.env)
            return it
        return None
