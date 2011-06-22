# -*- coding: utf-8 -*-

import os
from tempfile import mkstemp
from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.config import Option, FloatOption
from trac.env import IEnvironmentSetupParticipant
from trac.mimeview.api import IContentConverter, Context
from trac.util.translation import domain_functions

from tracstickyticket.pdf import PdfStickyTicket

add_domain, _ = domain_functions('tracstickyticket', 'add_domain', '_')

__all__ = ['StickyTicketModule']

class StickyTicketModule(Component):
    implements(IContentConverter, IEnvironmentSetupParticipant)

    _pagesize = Option('sticky-ticket', 'pagesize', 'A4',
        doc="Page size of PDF file which the tickets is printed")
    _sticky_width = FloatOption('sticky-ticket', 'sticky-width', '75',
        doc="Width (mm) of a sticky")
    _sticky_height = FloatOption('sticky-ticket', 'sticky-height', '75',
        doc="Height (mm) of a sticky")
    _fontname = Option('sticky-ticket', 'fontname', '(auto)',
        doc="Font name in PDF file")

    def __init__(self):
        Component.__init__(self)
        dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, dir)

    # IEnvironmentSetupParticipant
    def environment_created():
        pass

    def environment_needs_upgrade(db):
        return False

    def upgrade_environment(db):
        pass

    # IContentConverter
    def get_supported_conversions(self):
        yield ('sticky-ticket', _("Sticky"), 'pdf',
               'trac.ticket.Ticket', 'application/pdf', 8)
        yield ('sticky-query', _("Sticky"), 'pdf',
               'trac.ticket.Query', 'application/pdf', 8)

    def convert_content(self, req, mimetype, input, key):
        if key == 'sticky-query':
            return self._sticky_from_query(req, input)
        if key == 'sticky-ticket':
            return self._sticky_from_ticket(req, input)

    def _sticky_from_query(self, req, query):
        context = Context.from_request(req, 'query', absurls=True)
        for col in ('id', 'summary', 'type', 'description', 'time', 'reporter'):
            if col not in query.rows:
                query.rows.append(col)
        query.has_more_pages = False
        query.max = 0

        if hasattr(self.env, 'get_read_db'):
            db = self.env.get_read_db()
        else:
            db = self.env.get_db_cnx()
        tickets = query.execute(req, db)
        return self._sticky(req, tickets)

    def _sticky_from_ticket(self, req, ticket):
        id = ticket.id
        ticket = ticket.values
        ticket['id'] = id
        return self._sticky(req, [ticket])

    def _sticky(self, req, tickets):
        stickysize = (self._sticky_width, self._sticky_height)
        fontname = self._fontname
        locale = None
        if hasattr(req, 'locale'):
            locale = str(req.locale)

        f = None
        fd, filename = mkstemp()
        try:
            pdf = PdfStickyTicket(filename, tickets, pagesize=self._pagesize,
                                  stickysize=stickysize, fontname=fontname,
                                  locale=locale)
            pdf.generate()
            f = os.fdopen(fd)
            try:
                output = f.read()
            finally:
                f.close()
        finally:
            if f is None:
                os.close(fd)
            os.unlink(filename)

        return output, 'application/pdf'
