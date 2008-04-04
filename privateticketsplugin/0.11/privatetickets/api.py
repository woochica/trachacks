from trac.core import *
from trac.perm import IPermissionRequestor, IPermissionGroupProvider, PermissionSystem
from trac.ticket.model import Ticket
from trac.config import IntOption, ListOption

try:
    set = set
except NameError:
    from sets import Set as set

__all__ = ['PrivateTicketsSystem']

class PrivateTicketsSystem(Component):
    """Central tasks for the PrivateTickets plugin."""
    
    implements(IPermissionRequestor)
    
    group_providers = ExtensionPoint(IPermissionGroupProvider)

    blacklist = ListOption('privatetickets', 'group_blacklist', default='anonymous, authenticated',
                           doc='Groups that do not affect the common membership check.')
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        actions = ['TICKET_VIEW_REPORTER', 'TICKET_VIEW_OWNER', 'TICKET_VIEW_CC']
        group_actions = ['TICKET_VIEW_REPORTER_GROUP', 'TICKET_VIEW_OWNER_GROUP', 'TICKET_VIEW_CC_GROUP'] 
        all_actions = actions + [(a+'_GROUP', [a]) for a in actions]
        return all_actions + [('TICKET_VIEW_SELF', actions), ('TICKET_VIEW_GROUP', group_actions)]

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

        if req.perm.has_permission('TICKET_VIEW_CC') and \
           req.authname in [x.strip() for x in tkt['cc'].split(',')]:
            return True

        if req.perm.has_permission('TICKET_VIEW_OWNER') and \
           req.authname == tkt['owner']:
            return True            
            
        if req.perm.has_permission('TICKET_VIEW_REPORTER_GROUP') and \
           self._check_group(req.authname, tkt['reporter']):
            return True

        if req.perm.has_permission('TICKET_VIEW_OWNER_GROUP') and \
           self._check_group(req.authname, tkt['owner']):
            return True
            
        if req.perm.has_permission('TICKET_VIEW_CC_GROUP'):
            for user in tkt['cc'].split(','):
                #self.log.debug('Private: CC check: %s, %s', req.authname, user.strip())
                if self._check_group(req.authname, user.strip()):
                    return True
                    
        return False

    # Internal methods
    def _check_group(self, user1, user2):
        """Check if user1 and user2 share a common group."""
        user1_groups = self._get_groups(user1)
        user2_groups = self._get_groups(user2)
        both = user1_groups.intersection(user2_groups)
        both -= set(self.blacklist)

        #self.log.debug('PrivateTicket: %s&%s = (%s)&(%s) = (%s)', user1, user2, ','.join(user1_groups), ','.join(user2_groups), ','.join(both))
        return bool(both)

    def _get_groups(self, user):
        # Get initial subjects
        groups = set([user])
        for provider in self.group_providers:
            for group in provider.get_permission_groups(user):
                groups.add(group)
                
        perms = PermissionSystem(self.env).get_all_permissions()
        repeat = True
        while repeat:
            repeat = False
            for subject, action in perms:
                if subject in groups and action.islower() and action not in groups:
                    groups.add(action)
                    repeat = True 
                    
        return groups
        