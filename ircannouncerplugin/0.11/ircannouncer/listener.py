# -*- coding: utf-8 -*-
"""
    ircannouncer.listener
    ~~~~~~~~~~~~~~~~~~~~~

    This part of the plugin implements the listeners used by the script
    to send the changes to a supybot.

    :copyright: Copyright 2007 by Armin Ronacher.
    :license: BSD.
"""
import posixpath
from trac.config import *
from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.versioncontrol.api import IRepositoryListener
from xmlrpclib import ServerProxy


class IRCAnnouncerListener(Component):
    implements(ITicketChangeListener, IRepositoryListener)

    bot_interface_address = Option('ircannouncer', 'bot_interface_address',
        '', "The address of the bot interface.  eg: `127.0.0.0:7890`")

    def __init__(self):
        self.bot = ServerProxy('http://%s/' % self.bot_interface_address)

    def notify(self, type, title, lines):
        """Notify the bot about some changes."""
        self.bot.ircannouncer.notify(type, self.env.project_name,
                                     self.env.project_url,
                                     title, lines)

    # -- ITicketChangeListener

    def ticket_create(self, ticket):
        self.notify('ticket', '#%s (%s): created' % (ticket.id, ticket.

    def ticket_changed(self, ticket, comment, author, old_values):
        pass

    def ticket_deleted(self, ticket):
        pass

    # -- IRepositoryListener

    def changeset_synced(self, chgset):
        pass

    def changeset_commited(self, chgset):
        outer_path = None
        files = 0
        for path, kind, change, base_path, base_rev in chgset.get_changes():
            directory = posixpath.diranme(path)
            if outer_path is None:
                outer_path = directory
            else:
                outer_path = posixpath.commonprefix((outer_path, directory))
            files += 1
        self.notify('changeset', '[%s] (%s):' % (chgset.rev, chgset.author), [
            u'  * changes in %d files in %s' % (files, outer_path),
        ] + [u'    ' + x for x in chgset.message.splitlines()])
