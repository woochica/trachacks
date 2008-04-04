# Created by  on 2008-04-04.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.

from trac.core import *
from trac.perm import IPermissionRequestor, IPermissionPolicy
from trac.ticket.model import Ticket
from trac.config import IntOption, ListOption
from trac.util.compat import set

__all__ = ['PrivateTicketsSystem']


class PrivateTicketsSystem(Component):
    """Central tasks for the PrivateTickets plugin."""
    
    implements(IPermissionRequestor, IPermissionPolicy)
    
    group_providers = ExtensionPoint(IPermissionGroupProvider)
    
    blacklist = ListOption('privatetickets', 'group_blacklist', default='anonymous, authenticated',
                           doc='Groups that do not affect the common membership check.')
    
    # IPermissionPolicy(Interface)
    def check_permission(self, action, username, resource, perm):
        if username == 'anonymous' or resource is None:
            return None
        if resource.realm == 'ticket' and action == 'TICKET_VIEW':
            return self.check_ticket_access(perm, resource)
        return None
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        actions = ['TICKET_VIEW_REPORTER', 'TICKET_VIEW_OWNER', 'TICKET_VIEW_CC']
        group_actions = ['TICKET_VIEW_REPORTER_GROUP', 'TICKET_VIEW_OWNER_GROUP', 'TICKET_VIEW_CC_GROUP'] 
        all_actions = actions + [(a+'_GROUP', [a]) for a in actions]
        return all_actions + [('TICKET_VIEW_SELF', actions), ('TICKET_VIEW_GROUP', group_actions)]
    
    # Public methods
    def check_ticket_access(self, perm, res):
        """Return if this req is permitted access to the given ticket ID."""
        try:
            tkt = Ticket(self.env, res.id)
        except TracError:
            return False # Ticket doesn't exist
        
        if perm.has_permission('TICKET_VIEW_REPORTER') and \
           tkt['reporter'] == perm.username:
            return True
        
        if perm.has_permission('TICKET_VIEW_CC') and \
           perm.username in [x.strip() for x in tkt['cc'].split(',')]:
            return True
        
        if perm.has_permission('TICKET_VIEW_OWNER') and \
           perm.username == tkt['owner']:
            return True
        
        if perm.has_permission('TICKET_VIEW_REPORTER_GROUP') and \
           self._check_group(perm.username, tkt['reporter']):
            return True
        
        if perm.has_permission('TICKET_VIEW_OWNER_GROUP') and \
           self._check_group(perm.username, tkt['owner']):
            return True
        
        if perm.has_permission('TICKET_VIEW_CC_GROUP'):
            for user in tkt['cc'].split(','):
                #self.log.debug('Private: CC check: %s, %s', req.authname, user.strip())
                if self._check_group(perm.username, user.strip()):
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