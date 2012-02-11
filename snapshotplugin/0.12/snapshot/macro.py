#!/bin/env python
# -*- coding: utf-8 -*-
from genshi.builder import tag
from trac.core import Component, implements
from trac.ticket.api import TicketSystem
from trac.util.translation import _
from trac.web.chrome import Chrome, add_stylesheet
from trac.wiki.api import IWikiMacroProvider
import sys

class QueryResults(Component):
    implements (IWikiMacroProvider)
    
    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'QueryResults'

    def expand_macro(self, formatter, name, content, args=[]):
        try:
            cols = [] # Centinel
            group = '' # Centinel
            groups = {}
            lines = content.split('\r\n')
            for line in lines:
                if line.startswith('||= href =||= '):
                    cols = line[14:].split(' =||= ')
                elif line.startswith('|| group: '):
                    group = line[10:]
                    if group == u'None': group = None
                    groups[group] = [] # initialize for the group
                elif line.startswith('|| '):
                    values = iter(line[3:].split(' || '))
                    ticket = { 'href': values.next() }
                    for col in cols:
                        ticket[col] = values.next()
                    groups[group].append(ticket)
                else:
                    pass
            ticketsystem = TicketSystem(self.env)
            #
            labels = ticketsystem.get_ticket_field_labels()
            headers = [{ 'name': col, 'label': labels.get(col, _('Ticket'))} for col in cols]
            #
            fields = {}
            ticket_fields = ticketsystem.get_ticket_fields()
            for field in ticket_fields:
                fields[field['name']] = {'label': field['label']} # transform list to expected dict
            # fail safe
            fields[None] = 'NONE'
            for group in groups.keys():
                if not fields.has_key(group):
                    fields[group] = group
            #
            group_name = 'group' in args and args['group'] or None
            if group_name not in fields: group_name = None
            query = {'group':group_name}
            #
            groups = [(name, groups[name]) for name in groups] # transform dict to expected tuple
            #
            data = {
                'paginator': None,
                'headers': headers,
                'query': query,
                'fields': fields,
                'groups': groups,
            }
            add_stylesheet(formatter.req, 'common/css/report.css')
            chrome = Chrome(self.env)
            data = chrome.populate_data(formatter.req, data)
            template = chrome.load_template('query_results.html')
            content = template.generate(**data)
            return tag.div(content)
        except StopIteration:
            errorinfo = _('Not Enough fields in ticket: %s') % line
        except Exception:
            errorinfo = sys.exc_info()
        return tag.div(tag.div(errorinfo, class_='message'), class_='error', id='content')
