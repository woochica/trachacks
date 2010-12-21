from trac.core import *
from trac.perm import IPermissionPolicy, IPermissionRequestor
from trac.config import ListOption

class SecureTicketsPolicy(Component):
    """Prevent access to tickets with specific components.
    
    Add the SECURE_TICKET_VIEW permission as a pre-requisite to view
    tickets whose components are not in a configurable "public" list.
    
    Once this plugin is enabled, you'll have to insert it at the
    appropriate place in your list of permission policies, e.g.
    {{{
    [trac]
    permission_policies = SecurityTicketsPolicy, AuthzPolicy, 
                          DefaultPermissionPolicy, LegacyAttachmentPolicy
    }}}
    """
    
    public_components = ListOption('securetickets', 'public_components',
        default=[], doc="components whose tickets do not require " +
                        "SECURE_TICKET_VIEW permission to view.")
    
    implements(IPermissionPolicy, IPermissionRequestor)
    
    
    # IPermissionPolicy methods
    
    def check_permission(self, action, username, resource, perm):
        # We add the 'SECURE_TICKET_VIEW' pre-requisite for any action
        # other than 'SECURE_TICKET_VIEW' itself, as this would lead
        # to recursion.
        if action == 'SECURE_TICKET_VIEW':
            return
        
        # Check whether we're dealing with a ticket resource
        while resource:
            if resource.realm == 'ticket':
                break
            resource = resource.parent
        
        if resource and resource.realm == 'ticket' and resource.id is not None:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT component FROM ticket WHERE id=%s",
                           (resource.id,))
            for (component,) in cursor: pass
            
            # any public component makes the ticket public
            for pc in self.public_components:
                if pc in component.split(', '): # handle component list
                    return None
                
            # not public!
            if 'SECURE_TICKET_VIEW' not in perm:
                return False
    
    
    # IPermissionRequestor methods
    
    def get_permission_actions(self):
        yield 'SECURE_TICKET_VIEW'
