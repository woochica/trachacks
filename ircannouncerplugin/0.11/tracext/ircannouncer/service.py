# -*- coding: utf-8 -*-
"""
    ircannouncer.service
    ~~~~~~~~~~~~~~~~~~~~

    This module implements a component the bot can use to get information
    about tickets or changesets.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from trac.core import *
from trac.web.main import IRequestHandler
from trac.ticket.model import Ticket
from trac.resource import ResourceNotFound
from trac.versioncontrol.api import NoSuchChangeset
from trac.wiki.model import WikiPage

from tracext.ircannouncer.utils import TracXMLRPCRequestHandler, \
     NotFound, prepare_ticket_values, prepare_changeset_values, \
     prepare_wiki_page_values


class BotService(Component):
    implements(IRequestHandler)

    def __init__(self):
        self.dispatcher = TracXMLRPCRequestHandler({
            'ircannouncer.getTicket':       self.get_ticket,
            'ircannouncer.getChangeset':    self.get_changeset,
            'ircannouncer.getWikiPage':     self.get_wiki_page
        })

    # -- RPC methods

    def get_ticket(self, req, ticket_id):
        try:
            ticket = Ticket(self.env, ticket_id)
        except ResourceNotFound:
            raise NotFound()
        return prepare_ticket_values(ticket)

    def get_changeset(self, req, ident):
        repo = self.env.get_repository()
        repo.sync()
        try:
            chgset = repo.get_changeset(ident)
        except NoSuchChangeset:
            raise NotFound()
        return prepare_changeset_values(self.env, chgset)

    def get_wiki_page(self, req, page_name):
        page = WikiPage(self.env, page_name)
        if not page.exists:
            raise NotFound()
        return prepare_wiki_page_values(page)

    # -- IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/ircannouncer_service'

    def process_request(self, req):
        self.dispatcher.dispatch(req)
