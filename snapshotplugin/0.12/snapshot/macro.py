#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag
from trac.core import Component, implements
from trac.ticket.api import TicketSystem
from trac.util.translation import _
from trac.web.chrome import Chrome, add_stylesheet
from trac.wiki.api import IWikiMacroProvider
import sys
from trac.wiki.formatter import format_to_html


class QueryResults(Component):
    """ Show following static data in query table format. """
    implements(IWikiMacroProvider)

    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'QueryResults'

    def get_macro_description(self, name):
        return """ @param group=column_name (Optional)
        Show following static data in query table format.
Example:
{{{
    {{{#!QueryResults(group=milestone)
    ||= href =||= id =||= summary =||= status =||= owner =||= time
    || group: milestone1
    || /trac/project1/ticket/1 || 1 || Example || accepted || admin || 2012/02/03 0:48:05
    || group:
    || /trac/project1/ticket/2 || 2 || Summary || assigned || matobaa || 2012/02/06 8:25:51
    || /trac/project1/ticket/3 || 3 || Closed || closed || admin || 2012/02/07 23:55:19
    || /trac/project1/ticket/4 || 4 || active ticket || new || somebody || 2012/02/11 15:21:29
    }}}
}}}"""

    def expand_macro(self, formatter, name, content, args=[]):
        try:
            cols = []  # Sentinel
            group = ''  # Sentinel
            groups = {}
            lines = content.split('\r\n')
            for line in lines:
                if line.startswith('||= href =||= '):
                    cols = line[14:].split(' =||= ')
                elif line.startswith('|| group: '):
                    group = line[10:]
                    if group in [u'', u'None']:
                        group = None
                    groups[group] = []  # initialize for the group
                elif line.startswith('|| '):
                    values = iter(line[3:].split(' || '))
                    ticket = {'href': values.next()}
                    for col in cols:
                        ticket[col] = values.next()
                    groups[group].append(ticket)
                else:
                    pass
            ticketsystem = TicketSystem(self.env)
            #
            labels = ticketsystem.get_ticket_field_labels()
            headers = [{'name': col, 'label': labels.get(col, _('Ticket'))} for col in cols]
            #
            fields = {}
            ticket_fields = ticketsystem.get_ticket_fields()
            for field in ticket_fields:
                fields[field['name']] = {'label': field['label']}  # transform list to expected dict
            # fail safe
            fields[None] = 'NONE'
            for group in groups.keys():
                if not 'group' in fields:
                    fields[group] = group
            #
            group_name = 'group' in args and args['group'] or None
            if group_name not in fields:
                group_name = None
            query = {'group': group_name}
            #
            groups = [(name, groups[name]) for name in groups]  # transform dict to expected tuple
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
            # ticket id list as static
            tickets = ''
            if 'id' in cols:
                ticket_id_list = [ticket.get('id') for group in groups for ticket in group[1]]
                if len(ticket_id_list) > 0:
                    tickets = '([ticket:' + ','.join(ticket_id_list) + ' query by ticket id])'
            return tag.div(content, format_to_html(self.env, formatter.context, tickets))
        except StopIteration:
            errorinfo = _('Not Enough fields in ticket: %s') % line
        except Exception:
            errorinfo = sys.exc_info()
        return tag.div(tag.div(errorinfo, class_='message'), class_='error', id='content')
