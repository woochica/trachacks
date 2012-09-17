# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Bart Ogryczak
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.ticket.api import ITicketChangeListener

from model import *

class BacklogTicketChangeListener(Component):
    "Listens to the changes of tickets and updates backlogs if necessary"

    implements(ITicketChangeListener)

    # ITicketChangeListener methods

    def ticket_created(self, ticket):
        """Called when a ticket is created."""

        backlog_name = ticket.values['backlog']
        if backlog_name != NO_BACKLOG:
            Backlog(self.env, name=backlog_name).add_ticket(ticket.id)

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified. Adds and removes tickets
        from backlogs."""

        backlog_name = ticket.values.get('backlog', NO_BACKLOG)

        # backlog has been changed
        if 'backlog' in old_values.keys():
            if backlog_name == NO_BACKLOG:
                if old_values['backlog'] and old_values['backlog'] != NO_BACKLOG:
                    Backlog(self.env, name=old_values['backlog']).delete_ticket(ticket.id)
            else:
                Backlog(self.env, name=backlog_name).add_ticket(ticket.id)

        # ticket reopened, but backlog not changed
        if old_values.get('status') == 'closed' and backlog_name != NO_BACKLOG:
            Backlog(self.env, name=backlog_name).reset_priority(ticket.id, only_if_deleted=True)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted"""

        backlog_name = ticket.values['backlog']
        if backlog_name != NO_BACKLOG:
            Backlog(self.env, name=old_values['backlog']).delete_ticket(ticket.id)

