# Plugin to remove TICKET_APPEND privileges for a predefined list of ticketIDs
# Copyright 2008 Daniel A. Atallah <datallah@pidgin.im>

from trac.config import ListOption
from trac.core import *
from trac.perm import IPermissionPolicy

__all__ = ['ReadOnlyTicketFilter']

class ReadOnlyTicketFilter(Component):

    """
    A PermissionPolicy to remove TICKET_APPEND privileges for a predefined list of ticketIDs

    Don't forget to integrate that plugin in the appropriate place in the
    list of permission policies:
      [trac]
      permission_policies = ReadOnlyTicketFilter, DefaultPermissionPolicy

    Then you can configure which tickets to make readonly
      [readonlyticket]
      ticket_list=414,515
    """

    implements(IPermissionPolicy)
        
    ticket_list = ListOption('readonlyticket', 'ticket_list', '',
            doc="""List of tickets that should be considered Read-Only for
            users that don't have the TICKET_ADMIN priviledge.""")

    def check_permission(self, action, username, resource, perm):
        # We only are filtering the actions that we care about
        if (action not in ['TICKET_APPEND', 'TICKET_CHGPROP', 'TICKET_EDIT_DESCRIPTION']):
            return

        if (resource and resource.realm == 'ticket' and resource.id is not None \
                    and str(resource.id) in self.ticket_list \
                    and 'TICKET_ADMIN' not in perm):
            return False

