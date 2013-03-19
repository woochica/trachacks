#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from pkg_resources import ResourceManager
from trac.core import Component, implements, TracError
from trac.ticket.query import Query
from trac.web.chrome import add_script, ITemplateProvider, add_script_data
from trac.wiki.api import IWikiMacroProvider
import re

re_param = re.compile("\$[a-zA-Z]+")


class Macro(Component):
    """ Provides [StatusHistoryChart] Macro. """

    implements(IWikiMacroProvider, ITemplateProvider)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('statushistorychart', ResourceManager().resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IWikiMacroProvider methods
    def get_macros(self):
        return ['StatusHistoryChart']

    def get_macro_description(self, name):
        return """Plot a graph of ticket's status change history.
 without arguments::
  If argument is omitted, use following:
  - Result for report or query, if used on report description.
  - Bound for milestone, if used on milestone description.
  - Your last query result. You Feeling Lucky!
 args::
  - If you want to add filter, use TracQuery#QueryLanguage.
 Yaxis options::
  Use '''{{{format}}}''' parameter in query for yaxis values.
  slash {{{/}}} separated column name or {{{*}}} for wildcard.
  default: {{{new/assigned/accepted/closed/*}}}

 Example::
   {{{
   [[StatusHistoryChart]]
   [[StatusHistoryChart(format=new/*/closed)]]
   [[StatusHistoryChart(owner=$USER&format=new/*/closed)]]
   [[StatusHistoryChart(type=$TYPE&format=new/*/closed)]]  (uses CGI parameter for $TYPE)
   }}}"""

    def expand_macro(self, formatter, name, content, args=None):
        query = None
        status_list = ['new', 'assigned', 'accepted', 'closed', '*']
        default_status = status_list.index('*')
        add_script(formatter.req, "statushistorychart/js/flot/jquery.flot.js")
#        add_script(formatter.req, "statushistorychart/js/flot/jquery.flot.time.js")  # for flot 0.8dev or later
        add_script(formatter.req, "statushistorychart/js/enabler.js")
        if(content):
            # replace parameters
            for match in reversed([match for match in re_param.finditer(content)]):
                param_name = match.group(0)
                if param_name == '$USER':
                    authname = formatter.req.authname
                    if authname == 'anonymous':
                        authname = 'anonymous||somebody'
                    content = content.replace(param_name, authname)
                else:
                    param_value = formatter.req.args.get(param_name[1:])
                    if param_value:
                        content = content.replace(param_name, param_value)
            # execute query
            query = Query.from_string(formatter.env, content)
            status_list = query.format and query.format.split('/') or status_list
            if '*' not in status_list:
                status_list.append('*')
            default_status = status_list.index('*')
        if(query and len(query.constraint_cols) > 0):
            result = query.execute() or [{'id': -1}]  # Sentinel for no result
            cond = "ticket.id in (%s)" % ', '.join([str(t['id']) for t in result])
        elif formatter.resource.realm == 'milestone':
            cond = "ticket.milestone='%s'" % formatter.resource.id
        elif('query_tickets' in formatter.req.session):  # You Feeling Lucky
            query_tickets = formatter.req.session.get('query_tickets', '')
            tickets = len(query_tickets) and query_tickets.split(' ') or ['-1']  # Sentinel for no result
            cond = "ticket.id in (%s)" % ', '.join(tickets)
        else:
            raise TracError("Currently %sMacro without content is not supported." % name)
        changes = [row for row in formatter.env.get_read_db().execute("""
                SELECT id, time, null, 'new'
                    FROM ticket
                    WHERE %s
                UNION
                SELECT id, ticket_change.time, oldvalue, newvalue
                    FROM ticket
                    JOIN ticket_change ON ticket.id = ticket_change.ticket
                    WHERE %s AND field='status'
                ORDER BY id, time
                """ % (cond, cond))]
        # transform (ticket, time, status)* ==> (ticket <>- status)*
        tid = 0  # position of ticket id
        tickets = {}
        for change in changes:
            ticket = tickets.get(change[tid])  # slot is exist, or
            if ticket is None:
                ticket = tickets[change[tid]] = []  # create new slot and use it
            ticket.append(change)
        # group status_list
#        groupstats = self.compmgr[DefaultTicketGroupStatsProvider]
#        ticket_groups = groupstats._get_ticket_groups()
#        for group in ticket_groups:
#            pass
        # generate data
        data = []
        # points
        too_many_tickets = len(tickets) > 200
        for no, tid in enumerate(sorted(tickets)):
            if not too_many_tickets or tickets[tid][-1][3] != 'closed':
                void, time, void, state = tickets[tid][-1]  # @UnusedVariable
                index = state not in status_list and default_status or status_list.index(state)
                data.append({'points': {'show': True, 'radius': 8, 'color': no},
                             'label': tid,
                             'data': [[time / 1000, index]]})
        # lines
        for no, tid in enumerate(sorted(tickets)):
            data.append({'color': no, 'label': tid,
                         'data': [[time / 1000, state not in status_list and default_status or status_list.index(state)]
                                  for void, time, void, state in tickets[tid]]})  # @UnusedVariable
        # render
        add_script_data(formatter.req, {'statushistorychart_yaxis': status_list})
        add_script_data(formatter.req, {'statushistorychart_data': data})
        return '<div id="statushistorychart" style="width: 800px; height: 400px;"></div>'
