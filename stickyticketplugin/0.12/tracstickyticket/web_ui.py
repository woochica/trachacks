# -*- coding: utf-8 -*-

import os
import re
from tempfile import mkstemp
from pkg_resources import resource_filename

from trac.config import Option, FloatOption, ListOption
from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from trac.mimeview.api import IContentConverter, Context
from trac.resource import Resource
from trac.ticket.api import TicketSystem
from trac.ticket.query import Query
from trac.util.translation import domain_functions
from trac.web.api import IRequestFilter
from trac.web.chrome import add_link

from tracstickyticket.pdf import PdfStickyTicket

add_domain, _ = domain_functions('tracstickyticket', 'add_domain', '_')

__all__ = ['StickyTicketModule']

class StickyTicketModule(Component):
    implements(IContentConverter, IRequestFilter, IEnvironmentSetupParticipant)

    _pagesize = Option('sticky-ticket', 'pagesize', 'A4',
        doc="Page size of PDF file which the tickets is printed")
    _sticky_width = FloatOption('sticky-ticket', 'sticky-width', '75',
        doc="Width (mm) of a sticky")
    _sticky_height = FloatOption('sticky-ticket', 'sticky-height', '75',
        doc="Height (mm) of a sticky")
    _fontname = Option('sticky-ticket', 'fontname', '(auto)',
        doc="Font name in PDF file")
    _fields = ListOption('sticky-ticket', 'fields', 'owner,reporter,time',
        doc="Ticket fields in a sticky")

    def __init__(self):
        Component.__init__(self)
        dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, dir)

    # IEnvironmentSetupParticipant
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        return False

    def upgrade_environment(self, db):
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

    _report_request_match = re.compile(r'/report/[0-9]+\Z').match

    # IRequestFilter
    def pre_process_request(self, req, handler):
        if self._report_request_match(req.path_info) \
                and req.args.get('format') == 'sticky-report' \
                and handler.__class__.__name__ == 'ReportModule':
            req.args['max'] = 0
        return handler

    def post_process_request(self, req, template, data, content_type):
        if data and template == 'report_view.html':
            if req.args.get('format') == 'sticky-report':
                content, content_type = self._sticky_from_report(req, data)
                req.send(content, content_type)
            else:
                self._add_alternate_links(req)
        return template, data, content_type

    # internal
    def _add_alternate_links(self, req):
        url = '?format=sticky-report'
        if req.query_string:
            url += '&' + req.query_string
        add_link(req, 'alternate', url, _("Sticky"), 'application/pdf',
                 'pdf')

    def _sticky_from_query(self, req, query):
        context = Context.from_request(req, 'query', absurls=True)
        for col in ['id', 'summary', 'type'] + self._fields:
            if col not in query.rows:
                query.rows.append(col)
        query.has_more_pages = False
        query.max = 0

        if hasattr(self.env, 'get_read_db'):
            db = self.env.get_read_db()
        else:
            db = self.env.get_db_cnx()
        tickets = []
        for ticket in query.execute(req, db):
            resource = Resource('ticket', ticket['id'])
            if 'TICKET_VIEW' in req.perm(resource):
                tickets.append(ticket)
        return self._sticky(req, tickets)

    def _sticky_from_ticket(self, req, ticket):
        id = ticket.id
        ticket = ticket.values
        ticket['id'] = id
        return self._sticky(req, [ticket])

    def _sticky_from_report(self, req, data):
        ids = []
        for value_for_group, row_group in data['row_groups']:
            ids.extend([int(row['id']) for row in row_group
                        if row['resource'] and
                           row['resource'].realm == 'ticket' and
                           'TICKET_VIEW' in req.perm(row['resource'])])
        cols = ['id', 'summary', 'type']
        for col in self._fields:
            if col not in cols:
                cols.append(col)
        if hasattr(self.env, 'get_read_db'):
            db = self.env.get_read_db()
        else:
            db = self.env.get_db_cnx()
        start = 0
        count = 100
        tickets = []
        while start < len(ids):
            constraints = [{
                'id': ','.join(str(id) for id in ids[start:start + count])
            }]
            query = Query(self.env, constraints=constraints, cols=cols, max=0)
            tickets.extend(query.execute(req, db))
            start += count
        tickets_dict = dict((int(ticket['id']), ticket) for ticket in tickets)
        tickets = [tickets_dict[id] for id in ids if id in tickets_dict]
        return self._sticky(req, tickets)

    def _sticky(self, req, tickets):
        fields = dict((f['name'], f)
                      for f in TicketSystem(self.env).get_ticket_fields())
        fields = [fields[f] for f in self._fields if f in fields]
        stickysize = (self._sticky_width, self._sticky_height)
        fontname = self._fontname

        f = None
        fd, filename = mkstemp()
        try:
            pdf = PdfStickyTicket(filename, tickets, fields, req,
                                  pagesize=self._pagesize,
                                  stickysize=stickysize, fontname=fontname)
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
