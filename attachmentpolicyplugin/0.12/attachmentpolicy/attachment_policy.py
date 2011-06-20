from trac.core import Component, implements
from trac.perm import IPermissionPolicy, IPermissionRequestor

class AttachmentDeletePolicy(Component):
    """Adds permission `TICKET_ATTACHMENT_DELETE` for exclusive right to delete and replace 
attachments, regardless who added / changed it.

Everybody who has permission `TICKET_ATTACHMENT_DELETE` can delete / replace attachments, 
regardless who added / changed it.

Once this plugin is enabled, you'll have to insert it at the appropriate
place in your list of permission policies, e.g.
{{{
[trac]
permission_policies = AttachmentDeletePolicy, DefaultPermissionPolicy, LegacyAttachmentPolicy
}}}
"""
    implements(IPermissionPolicy, IPermissionRequestor)
    
    # IPermissionPolicy methods
    def check_permission(self, action, username, resource, perm):
        # We add the 'TICKET_ATTACHMENT_DELETE' pre-requisite for any action
        # other than 'TICKET_ATTACHMENT_DELETE' itself, as this would lead
        # to recursion. (copied from sample-plugins/permissions/vulnerability_tickets.py)
        if action == 'TICKET_ATTACHMENT_DELETE':
            return
        
#        self.log.info( "action: %s, resource: %s" % (action, resource) )
        # Check whether we're dealing with a ticket resource
        if action and action == 'ATTACHMENT_DELETE' \
        and resource and resource.realm == 'attachment' \
        and 'TICKET_ATTACHMENT_DELETE' in perm:
            self.log.info( "granted permission for user %s deleting attachment %s" % (username, resource) )
            return True
    
    # IPermissionRequestor methods    
    def get_permission_actions(self):
        yield 'TICKET_ATTACHMENT_DELETE'