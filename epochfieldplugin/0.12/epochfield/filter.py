# -*- coding: utf-8 -*-

from datetime import datetime
from genshi.builder import tag
from genshi.filters.transform import Transformer
from pkg_resources import ResourceManager
from trac.cache import cached
from trac.core import Component, implements
from trac.ticket.api import ITicketManipulator, TicketSystem
from trac.ticket.model import Ticket
from trac.util.datefmt import format_datetime, from_utimestamp, to_timestamp, \
    format_date, format_time
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import add_script, ITemplateProvider, add_stylesheet
import re

is_trac_ja = ResourceManager().resource_exists('trac.wiki', 'default-pages/TracJa')
# Is patch need or not, for trac-ja from interact
# https://twitter.com/#!/jun66j5/status/180856879155658753 by @jun66j5;
# "まともな方法がなくて、前にやったのは trac/wiki/default-pages/TracJa
# があるかどうかを pkg_resources.resource_filename で調べてました"

class EpochField(Component):
    implements(ITemplateStreamFilter, ITemplateProvider, IRequestFilter, ITicketManipulator)
    
    @classmethod
    def should_be_ignored(self, col):    
        "because of translated in report_view.html, I don't replace them "
        return col in ['time', 'date', 'created', 'modified', 'datetime'] or \
            is_trac_ja and any(map(col.endswith, [u'日付', u'日時', u'時刻'])) or False

    _format = '%Y-%m-%d %H:%M:%S'   # NOTE: match a format in epochfield.js
    
    def _e2s(self, req, data):
        """ Epoch to String """
        return data.isdigit() and format_datetime(from_utimestamp(long(data)), self._format, req.tz) or data

    def _s2e(self, req, data):
        """ String to Epoch """
        try:
            dt = datetime.strptime(data, self._format).replace(tzinfo=req.tz)
            dt.astimezone(req.tz)
            return str(to_timestamp(dt) * 1000 * 1000)
        except Exception as e:
            self.log.debug(e)
            pass
        return data
    
    @cached
    def epoch_fields_name(self, db):
        fields = TicketSystem(self.env).get_ticket_fields()
        return [field.get('name') for field in fields if field.get('format') == 'epoch']

    @cached
    def function_map(self, db):
        """ map between translator method and field-names will be translated """
        matcher = lambda x : re.compile(x + '$')
        return [
            (format_date, map(matcher, self.config.getlist('epochfield', 'date_columns', default='.*_date'))),
            (format_time, map(matcher, self.config.getlist('epochfield', 'time_columns', default='.*_time'))),
            (format_datetime, map(matcher, self.config.getlist('epochfield', 'datetime_columns', default='.*_datetime')
                                  + self.epoch_fields_name))
        ]

    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):
        """ String to Epoch, when modify ticket """
        for key in [key for key in ticket._old.keys() if key in self.epoch_fields_name]:
            ticket.values[key] = self._s2e(req, ticket.values[key])
        return [] # returns no errors

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('epochfield', ResourceManager().resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        return []
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template in ['ticket.html']: # e2s in ticket, changes, change_preview
            if 'ticket' in data and isinstance(data.get('ticket'), Ticket):
                values = data.get('ticket').values
                for e in self.epoch_fields_name:
                    if e in values:
                        values[e] = self._e2s(req, values[e])
            changes = data.get('changes', [])[:] # shallow copy
            if 'change_preview' in data:
                changes += [data.get('change_preview')]
            for change in changes:
                fields = change.get('fields', [])
                for field in [fields[e] for e in self.epoch_fields_name if e in fields]:
                    if 'old' in field:
                        field['old'] = self._e2s(req, field['old'])
                    if 'new' in field:
                        field['new'] = self._e2s(req, field['new'])
        if template in ['query.html']: # e2s in result
            for results in [group for ignored, group in data.get('groups')]:
                for values in results:
                    for e in self.epoch_fields_name:
                        if e in values:
                            values[e] = self._e2s(req, values[e])
        if template in ['report_view.html']: # e2s in specified fields in trac.ini
            for row_group in [r for ignored, r in data.get('row_groups', [])]:
                for row in row_group:
                    for cell_group in [c for c in row.get('cell_groups', [])]:
                        for cell in cell_group:
                            if cell.has_key('header') and cell.has_key('value'):
                                col = cell.get('header').get('col')
                                if EpochField.should_be_ignored(col): continue
                                value = cell['value']
                                for formatter, matchers in self.function_map:
                                    for matcher in matchers:
                                        if matcher.match(col):
                                            cell['value'] = value.isdigit() \
                                                and formatter(from_utimestamp(long(value)), tzinfo=req.tz) \
                                                or '--'
        return (template, data, content_type)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename in ['ticket.html']:
            add_stylesheet(req, 'epochfield/css/jquery.datetimeentry.css')
            add_script(req, 'epochfield/js/jquery.datetimeentry.js')
            add_script(req, 'epochfield/js/epochfield.js')
            for field in self.epoch_fields_name:
                stream |= Transformer() \
                            .select('//input[@id="field-' + field + '"]') \
                            .attr('class', 'datetimeEntry')
        return stream

class CustomFieldAdminTweak(Component):
    implements(ITemplateStreamFilter)
    
    def filter_stream(self, req, method, filename, stream, data):
        if filename in ['customfieldadmin.html']:
            stream = stream | Transformer('//select[@id="format"]').append(
                tag.option('Epoch', value='epoch')
            )
        return stream
