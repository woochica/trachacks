# -*- coding: utf-8 -*-

from trac.ticket import ITicketChangeListener
from trac.core import Component, implements

from manager import WorkLogManager


class WorkLogTicketObserver(Component):
    implements(ITicketChangeListener)

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        pass
    
    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.
        
        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        if self.config.getbool('worklog', 'autostop') \
               and 'closed' == ticket['status'] \
               and old_values.has_key('status') \
               and 'closed' != old_values['status']:
            mgr = WorkLogManager(self.env, self.config)
            who,since = mgr.who_is_working_on(ticket.id)
            if who:
                mgr = WorkLogManager(self.env, self.config, who)
                mgr.stop_work()

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        pass

