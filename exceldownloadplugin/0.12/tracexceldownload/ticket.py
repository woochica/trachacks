# -*- coding: utf-8 -*-

import re
from datetime import datetime
from itertools import chain
from xlwt import Workbook, Formula

from trac.core import Component, implements
from trac.mimeview.api import Context, IContentConverter
from trac.resource import Resource, get_resource_url
from trac.ticket.model import Ticket
from trac.ticket.query import Query
from trac.ticket.web_ui import TicketModule
from trac.util.datefmt import from_utimestamp
from trac.util.text import unicode_urlencode
from trac.util.translation import dgettext, dngettext
from trac.web.api import IRequestFilter, RequestDone
from trac.web.chrome import Chrome, add_link

from tracexceldownload.api import WorksheetWriter, get_workbook_content, \
                                  get_literal
from tracexceldownload.translation import _


__all__ = ['ExcelTicketModule']


class ExcelTicketModule(Component):

    implements(IContentConverter)

    def get_supported_conversions(self):
        yield ('excel', _("Excel"), 'xls',
               'trac.ticket.Query', 'application/vnd.ms-excel', 8)
        yield ('excel-history', _("Excel including history"), 'xls',
               'trac.ticket.Query', 'application/vnd.ms-excel', 8)
        yield ('excel-history', _("Excel including history"), 'xls',
               'trac.ticket.Ticket', 'application/vnd.ms-excel', 8)

    def convert_content(self, req, mimetype, content, key):
        if key == 'excel':
            return self._convert_query(req, content)
        if key == 'excel-history':
            kwargs = {}
            if isinstance(content, Ticket):
                content = Query.from_string(self.env, 'id=%d' % content.id)
                kwargs['sheet_query'] = False
                kwargs['sheet_history'] = True
            else:
                kwargs['sheet_query'] = True
                kwargs['sheet_history'] = True
            return self._convert_query(req, content, **kwargs)

    def _convert_query(self, req, query, sheet_query=True,
                       sheet_history=False):
        # no paginator
        query.max = 0
        query.has_more_pages = False
        query.offset = 0

        # extract all fields
        cols = ['id']
        cols += [field['name'] for field in query.fields]
        for name in ('time', 'changetime'):
            if name not in cols:
                cols.append(name)
        query.cols = cols

        db = self.env.get_read_db()
        tickets = query.execute(req, db)
        context = Context.from_request(req, 'query', absurls=True)
        data = query.template_data(context, tickets)

        book = Workbook(encoding='utf-8', style_compression=1)
        if sheet_query:
            self._create_sheet_query(req, context, data, book)
        if sheet_history:
            self._create_sheet_history(req, context, data, book)
        return get_workbook_content(book), 'application/vnd.ms-excel'

    def _create_sheet_query(self, req, context, data, book):
        sheet = book.add_sheet(dgettext('messages', 'Custom Query'))
        writer = WorksheetWriter(sheet, req)
        query = data['query']
        groups = data['groups']
        fields = data['fields']
        headers = data['headers']

        writer.write_row([(
            u'%s (%s)' % (dgettext('messages', 'Custom Query'),
                          dngettext('messages', '%(num)s match',
                                    '%(num)s matches', query.num_items)),
            'header', -1, -1)])
        for groupname, results in groups:
            if groupname:
                cell = fields[query.group]['label'] + ' '
                if query.group in ('owner', 'reporter'):
                    cell += Chrome(self.env).authorinfo(req, groupname)
                else:
                    cell += groupname
                cell += ' (%s)' % dngettext('messages', '%(num)s match',
                                            '%(num)s matches', len(results))
                writer.write_row([(cell, 'header2', -1, -1)])

            writer.write_row(
                (header['label'], 'thead', None, None)
                for idx, header in enumerate(headers))

            for result in results:
                ticket_context = context('ticket', result['id'])
                if 'TICKET_VIEW' not in req.perm(ticket_context.resource):
                    continue
                cells = []
                for idx, header in enumerate(headers):
                    name = header['name']
                    value, style, width, line = self._get_cell_data(
                            name, result[name], req, ticket_context, writer)
                    cells.append((value, style, width, line))
                writer.write_row(cells)
            writer.row_idx += 1    # blank row

        writer.set_col_widths()

    def _create_sheet_history(self, req, context, data, book):
        sheet = book.add_sheet(dgettext("messages", "Change History"))
        writer = WorksheetWriter(sheet, req)

        groups = data['groups']
        headers = [header for header in data['headers']
                   if header['name'] not in ('id', 'time', 'changetime')]
        headers[0:0] = [
            {'name': 'id', 'label': dgettext("messages", "Ticket")},
            {'name': 'time', 'label': dgettext("messages", "Time")},
            {'name': 'author', 'label': dgettext("messages", "Author")},
            {'name': 'comment', 'label': dgettext("messages", "Comment")},
        ]

        writer.write_row(
            (header['label'], 'thead', None, None)
            for idx, header in enumerate(headers))

        mod = TicketModule(self.env)
        for result in chain(*[results for groupname, results in groups]):
            id = result['id']
            ticket = Ticket(self.env, id)
            ticket_context = context('ticket', id)
            values = ticket.values.copy()
            changes = []

            for change in mod.rendered_changelog_entries(req, ticket):
                if change['permanent']:
                    changes.append(change)
            for change in reversed(changes):
                change['values'] = values
                values = values.copy()
                for name, field in change['fields'].iteritems():
                    if name in values:
                        values[name] = field['old']
            changes[0:0] = [{'date': ticket['time'], 'fields': {},
                             'values': values, 'cnum': None,
                             'comment': '', 'author': ticket['reporter']}]

            for change in changes:
                cells = []
                for idx, header in enumerate(headers):
                    name = header['name']
                    if name == 'id':
                        value = id
                    elif name == 'time':
                        value = change.get('date', '')
                    elif name == 'comment':
                        value = change.get('comment', '')
                    elif name == 'author':
                        value = change.get('author', '')
                    else:
                        value = change['values'].get(name, '')
                    value, style, width, line = \
                            self._get_cell_data(name, value, req,
                                                ticket_context, writer)
                    if name in change['fields']:
                        style = '%s:change' % style
                    cells.append((value, style, width, line))
                writer.write_row(cells)

        writer.set_col_widths()

    def _get_cell_data(self, name, value, req, context, writer):
        if name == 'id':
            url = req.abs_href.ticket(value)
            value = '#%d' % value
            width = len(value)
            value = Formula('HYPERLINK("%s",%s)' % (url, get_literal(value)))
            return value, 'id', width, 1

        if isinstance(value, datetime):
            return value, '[datetime]', None, None

        if value and name in ('reporter', 'owner'):
            value = Chrome(self.env).authorinfo(req, value)
            return value, name, None, None

        if name == 'cc':
            value = Chrome(self.env).format_emails(context, value)
            return value, name, None, None

        if name == 'milestone':
            url = req.abs_href.milestone(value)
            width, line = writer.get_metrics(value)
            value = Formula('HYPERLINK("%s",%s)' % (url, get_literal(value)))
            return value, name, width, line

        return value, name, None, None


class ExcelReportModule(Component):

    implements(IRequestFilter)

    _PATH_INFO_MATCH = re.compile(r'/report/[0-9]+').match

    def pre_process_request(self, req, handler):
        if self._PATH_INFO_MATCH(req.path_info) \
                and req.args.get('format') == 'xls' \
                and handler.__class__.__name__ == 'ReportModule':
            req.args['max'] = 0
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'report_view.html' and req.args.get('id'):
            format = req.args.get('format')
            if format == 'xls':
                resource = Resource('report', req.args['id'])
                data['context'] = Context.from_request(req, resource,
                                                       absurls=True)
                self._convert_report(req, data)
            elif not format:
                self._add_alternate_links(req)
        return template, data, content_type

    def _convert_report(self, req, data):
        book = Workbook(encoding='utf-8', style_compression=1)
        sheet = book.add_sheet(dgettext('messages', 'Report'))
        writer = WorksheetWriter(sheet, req)

        writer.write_row([(
            '%s (%s)' % (data['title'],
                         dngettext('messages', '%(num)s match',
                                   '%(num)s matches', data['numrows'])),
            'header', -1, -1)])

        for value_for_group, row_group in data['row_groups']:
            writer.row_idx += 1

            if value_for_group and len(row_group):
                writer.write_row([(
                    '%s (%s)' % (value_for_group,
                                 dngettext('messages', '%(num)s match',
                                           '%(num)s matches', len(row_group))),
                    'header2', -1, -1)])
            for header_group in data['header_groups']:
                writer.write_row([
                    (header['title'], 'thead', None, None)
                    for header in header_group
                    if not header['hidden']])

            for row in row_group:
                for cell_group in row['cell_groups']:
                    cells = []
                    for cell in cell_group:
                        cell_header = cell['header']
                        if cell_header['hidden']:
                            continue
                        col = cell_header['col'].strip('_').lower()
                        value, style, width, line = \
                                self._get_cell_data(req, col, cell, row, writer)
                        cells.append((value, style, width, line))
                    writer.write_row(cells)

        writer.set_col_widths()

        content = get_workbook_content(book)
        req.send_response(200)
        req.send_header('Content-Type', 'application/vnd.ms-excel')
        req.send_header('Content-Length', len(content))
        req.send_header('Content-Disposition',
                        'filename=report_%s.xls' % req.args['id'])
        req.end_headers()
        req.write(content)
        raise RequestDone

    def _get_cell_data(self, req, col, cell, row, writer):
        value = cell['value']

        if col == 'report':
            url = req.abs_href.report(value)
            width, line = writer.get_metrics(value)
            value = Formula('HYPERLINK("%s",%s)' % (url, get_literal(value)))
            return value, col, width, line

        if col in ('ticket', 'id'):
            value = '#%s' % cell['value']
            url = get_resource_url(self.env, row['resource'], req.abs_href)
            width = len(value)
            value = Formula('HYPERLINK("%s",%s)' % (url, get_literal(value)))
            return value, 'id', width, 1

        if col == 'milestone':
            url = req.abs_href.milestone(value)
            width, line = writer.get_metrics(value)
            value = Formula('HYPERLINK("%s",%s)' % (url, get_literal(value)))
            return value, col, width, line

        if col == 'time':
            if isinstance(value, basestring) and value.isdigit():
                value = from_utimestamp(long(value))
                return value, '[time]', None, None
        elif col in ('date', 'created', 'modified'):
            if isinstance(value, basestring) and value.isdigit():
                value = from_utimestamp(long(value))
                return value, '[date]', None, None
        elif col == 'datetime':
            if isinstance(value, basestring) and value.isdigit():
                value = from_utimestamp(long(value))
                return value, '[datetime]', None, None

        width, line = writer.get_metrics(value)
        return value, col, width, line

    def _add_alternate_links(self, req):
        params = {}
        for arg in req.args.keys():
            if not arg.isupper():
                continue
            params[arg] = req.args.get(arg)
        if 'USER' not in params:
            params['USER'] = req.authname
        if 'sort' in req.args:
            params['sort'] = req.args['sort']
        if 'asc' in req.args:
            params['asc'] = req.args['asc']
        href = ''
        if params:
            href = '&' + unicode_urlencode(params)
        add_link(req, 'alternate', '?format=xls' + href, _("Excel"),
                 'application/vnd.ms-excel')
