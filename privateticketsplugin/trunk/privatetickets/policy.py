# Created by Noah Kantrowitz on 2008-04-04.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.

from trac.core import *
from trac.perm import IPermissionRequestor, IPermissionGroupProvider, IPermissionPolicy, PermissionSystem
from trac.ticket.model import Ticket
from trac.config import IntOption, ListOption
from trac.util.compat import set

class PrivateTicketsPolicy(Component):
    """Central tasks for the PrivateTickets plugin."""
    
    implements(IPermissionRequestor, IPermissionPolicy)
    
    group_providers = ExtensionPoint(IPermissionGroupProvider)
    
    blacklist = ListOption('privatetickets', 'group_blacklist', default='anonymous, authenticated',
                           doc='Groups that do not affect the common membership check.')
    
    ignore_permissions = set([
        'TRAC_ADMIN',
        'TICKET_VIEW_REPORTER',
        'TICKET_VIEW_OWNER',
        'TICKET_VIEW_CC',
        'TICKET_VIEW_REPORTER_GROUP',
        'TICKET_VIEW_OWNER_GROUP',
        'TICKET_VIEW_CC_GROUP',
    ])
    
    # IPermissionPolicy(Interface)
    def check_permission(self, action, username, resource, perm):
        if username == 'anonymous' or \
           action in self.ignore_permissions or \
           'TRAC_ADMIN' in perm:
            # In these three cases, checking makes no sense
            return None
        
        # Look up the resource parentage for a ticket.
        while resource:
            if resource.realm == 'ticket':
                break
            resource = resource.parent
        if resource and resource.realm == 'ticket' and resource.id is not None:
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
            return None # Ticket doesn't exist
        
        had_any = False
        
        if perm.has_permission('TICKET_VIEW_REPORTER'):
            had_any = True
            if tkt['reporter'] == perm.username:
                return None
        
        if perm.has_permission('TICKET_VIEW_CC'):
            had_any = True
            if perm.username in [x.strip() for x in tkt['cc'].split(',')]:
                return None
        
        if perm.has_permission('TICKET_VIEW_OWNER'):
            had_any = True
            if perm.username == tkt['owner']:
                return None
        
        if perm.has_permission('TICKET_VIEW_REPORTER_GROUP'):
            had_any = True
            if self._check_group(perm.username, tkt['reporter']):
                return None
        
        if perm.has_permission('TICKET_VIEW_OWNER_GROUP'):
            had_any = True
            if self._check_group(perm.username, tkt['owner']):
                return None
        
        if perm.has_permission('TICKET_VIEW_CC_GROUP'):
            had_any = True
            for user in tkt['cc'].split(','):
                #self.log.debug('Private: CC check: %s, %s', req.authname, user.strip())
                if self._check_group(perm.username, user.strip()):
                    return None
        
        # No permissions assigned, punt
        if not had_any:
            return None
        
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
                if subject in groups and not action.isupper() and action not in groups:
                    groups.add(action)
                    repeat = True 
        
        return groups