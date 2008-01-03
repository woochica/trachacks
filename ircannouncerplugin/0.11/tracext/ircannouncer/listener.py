# -*- coding: utf-8 -*-
"""
    ircannouncer.listener
    ~~~~~~~~~~~~~~~~~~~~~

    This part of the plugin implements the listeners used by the script
    to send the changes to a supybot.

    :copyright: Copyright 2007 by Armin Ronacher.
    :license: BSD.
"""
from socket import error as SocketError
from xmlrpclib import ServerProxy

from trac.config import *
from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.versioncontrol.api import IRepositoryListener
from tracext.ircannouncer.utils import prepare_ticket_values, \
     prepare_changeset_values


class ChangeListener(Component):
    implements(ITicketChangeListener, IRepositoryListener)

    host = Option('ircannouncer', 'bot_host', '127.0.0.1',
        """The hostname / ip of the bot.  (eg: `127.0.0.1`)""")
    port = IntOption('ircannouncer', 'bot_port', '53312',
        """The port the port is listening on.  (eg: `53312`)""")

    def __init__(self):
        self.bot = ServerProxy('http://%s:%d/' % (self.host, self.port))

    def notify(self, type, values):
        """Notify the bot about some changes."""
        try:
            self.bot.ircannouncer.notify(type, values)
        except (IOError, SocketError):
            pass

    # -- ITicketChangeListener

    def ticket_created(self, ticket):
        values = prepare_ticket_values(ticket, 'created')
        self.notify('ticket', values)

    def ticket_changed(self, ticket, comment, author, old_values):
        values = prepare_ticket_values(ticket, 'changed')
        values.update({
            'comment':      comment,
            'author':       author,
            'old_values':   old_values
        })
        self.notify('ticket', values)

    def ticket_deleted(self, ticket):
        values = prepare_ticket_values(ticket, 'deleted')
        self.notify('ticket', values)

    # -- IRepositoryListener

    def changeset_synced(self, chgset):
        pass

    def changeset_commited(self, chgset):
        self.notify('changeset', prepare_changeset_values(chgset))
