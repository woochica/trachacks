# -*- coding: utf-8 -*-
"""
    ircannouncer.listener
    ~~~~~~~~~~~~~~~~~~~~~

    This part of the plugin implements the listeners used by the script
    to send the changes to a supybot.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from socket import error as SocketError
from xmlrpclib import ServerProxy, Fault

from trac.config import *
from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.versioncontrol.api import IRepositoryListener
from trac.wiki.api import IWikiChangeListener
from tracext.ircannouncer.utils import prepare_ticket_values, \
     prepare_changeset_values, prepare_wiki_page_values


class ChangeListener(Component):
    implements(ITicketChangeListener, IRepositoryListener,
               IWikiChangeListener)

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
        except (IOError, SocketError, Fault):
            return False
        return True

    # -- ITicketChangeListener

    def ticket_created(self, ticket):
        values = prepare_ticket_values(ticket, 'created')
        self.notify('ticket', values)

    def ticket_changed(self, ticket, comment, author, old_values):
        values = prepare_ticket_values(ticket, 'changed')
        values.update({
            'comment':      comment or '',
            'author':       author or '',
            'old_values':   old_values
        })
        self.notify('ticket', values)

    def ticket_deleted(self, ticket):
        pass

    # -- IRepositoryListener

    def changeset_synced(self, chgset):
        pass

    def changeset_commited(self, chgset):
        self.notify('changeset', prepare_changeset_values(self.env, chgset))

    # -- IWikiChangeListener

    def wiki_page_added(self, page):
        self.notify('wiki_page', prepare_wiki_page_values(page, 'added'))

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        values = prepare_wiki_page_values(page, 'changed')
        values['comment'] = comment or ''
        values['last_author'] = author or ''
        self.notify('wiki_page', values)

    def wiki_page_deleted(self, page):
        pass

    def wiki_page_version_deleted(self, page):
        pass
