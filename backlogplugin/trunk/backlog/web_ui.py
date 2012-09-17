# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Bart Ogryczak
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag
from trac.core import Component, implements
from trac.perm import IPermissionRequestor, PermissionCache, PermissionError
from trac.ticket.api import ITicketChangeListener, TicketSystem
from trac.util.translation import _
from trac.web import IRequestHandler
from trac.web.chrome import (
    INavigationContributor, ITemplateProvider, add_stylesheet, add_script
)

from db import create_ordering_table
from model import *

import re

TicketSystem.get_custom_fields_orig = TicketSystem.get_custom_fields

def custom_enum_fields(self):
    fields = self.get_custom_fields_orig()
    config = self.config['ticket-custom']

    for field in fields:
        if field['type'] == 'enum':
            field['type'] = 'select'
            name = field['name']
            enum_col = config.get(name + '.options')
            from trac.ticket.model import AbstractEnum
            enum_cls = type(str(enum_col), (AbstractEnum,), {})
            enum_cls.type = enum_col
            db = self.env.get_db_cnx()
            field['options'] = [val.name for val in enum_cls.select(self.env, db=db)]

    return fields

def get_custom_fields_w_backlog(self):
    fields = self.get_custom_fields_orig()
    config = self.config['ticket-custom']
    for field in fields:
        if field['type'] == 'backlog':
            field['type'] = 'select'
            name = field['name']
            assert name == 'backlog', 'this only works with predefined field name'
            enum_col = config.get(name + '.options')
            field['options'] = [val.name for val in BacklogList(self.env)]
            field['options'].insert(0, NO_BACKLOG)
    return fields
TicketSystem.get_custom_fields = get_custom_fields_w_backlog 


class BacklogModule(Component):
    implements(INavigationContributor, IRequestHandler,
               ITemplateProvider, IPermissionRequestor)

    # INavigationContributor methods


    def get_active_navigation_item(self, req):
        return 'backlog'

    def get_navigation_items(self, req):
        if 'BACKLOGS_VIEW' in req.perm:
            yield ('mainnav', 'backlog',
                   tag.a('Backlogs', href=req.href.backlog()))

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'^/backlog(?:/([0-9]+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['backlog_id'] = match.group(1)
            return True

    def process_request(self, req):
        req.perm.require('BACKLOGS_VIEW')
        db = self.env.get_db_cnx()
        create_ordering_table(db)
        backlog_id = req.args.get('backlog_id')
        if req.method == 'POST':
            self._save_order(req, backlog_id)
            req.redirect(req.href.backlog(backlog_id))

        add_script(req, 'backlog/js/jquery-ui-1.7.3.custom.min.js')
        add_stylesheet(req, 'backlog/css/jquery-ui-1.7.3.custom.css')
        add_stylesheet(req, 'backlog/css/backlog.css')

        if backlog_id:
            # TODO: check if backlog with ID exists
            return self._show_backlog(req, backlog_id)
        else:
            return self._show_backlog_list(req)

    def _show_backlog(self, req, backlog_id):

        backlog = Backlog(self.env, backlog_id)
        data = {}
        data['backlog'] = backlog
        data['tickets'], data['tickets2'] = backlog.get_tickets()

        if 'BACKLOG_MODIFY' in req.perm:
            add_script(req, 'backlog/js/backlog.rw.js')
        else:
            add_script(req, 'backlog/js/backlog.ro.js')

        return 'backlog.html', data, None

    def _show_backlog_list(self, req):
        db = self.env.get_db_cnx()
        backlog_id = req.args.get('backlog_id', None)

        columns = ['id', 'name', 'owner', 'description']

        cursor = db.cursor()
        sql = """SELECT %s, 0 as total, 0 as active
                 FROM  backlog
                 """ % (','.join(columns))
        cursor.execute(sql)

        columns.extend(['total', 'active'])

        data = {}
        data['backlogs'] = dict([(backlog[0], (dict(zip(columns, backlog)))) for backlog in cursor])

        # get total of tickets in each backlog
        sql = """SELECT bklg_id, count(*) as total
                 FROM backlog_ticket
                 WHERE tkt_order IS NULL OR tkt_order > -1
                 GROUP BY bklg_id
              """
        cursor.execute(sql)

        for id, total in cursor:
            data['backlogs'][id]['total'] = total
            data['backlogs'][id]['closed'] = 0
            data['backlogs'][id]['active'] = 0

        # get total of tickets by status in each backlog
        sql = """SELECT bt.bklg_id, t.status, count(*) as total
                 FROM backlog_ticket bt, ticket t
                 WHERE t.id = bt.tkt_id
                 AND (bt.tkt_order IS NULL OR bt.tkt_order > -1)
                 GROUP BY bklg_id, status
              """
        cursor.execute(sql)

        for id, status, total in cursor:
            if(status == 'closed'):
                data['backlogs'][id]['closed'] += total
            else:
                data['backlogs'][id]['active'] += total
            data['backlogs'][id]['status_%s' % status] = total

        return 'backlog_list.html', data, None

    def _save_order(self, req, backlog_id):
        backlog = Backlog(self.env, backlog_id)
        req.perm.require('BACKLOG_MODIFY')
        #db = self.env.get_db_cnx()
        #cursor = db.cursor()
        if req.args.get('delete_closed', '') != '':
            backlog.remove_closed_tickets()
        if req.args.get('ticket_order', '') != '':
            ticket_order = req.args.get('ticket_order', '').split(',')
            ticket_order = [int(tkt_id.split('_')[1]) for tkt_id in ticket_order]
            backlog.set_ticket_order(ticket_order)
            #ticket_order = [ (bklg_id, int(tkt_id.split('_')[1]), int(tkt_order)) for (tkt_order, tkt_id) in enumerate(ticket_order)]
            #cursor.executemany('REPLACE INTO backlog_tkt (bklg_id, tkt_id, tkt_order) VALUES (%s, %s, %s)', ticket_order)
        if req.args.get('tickets_out', '') != '':
            tickets_out = req.args.get('tickets_out', '').split(',')
            tickets_out = [ int(tkt_id.split('_')[1]) for tkt_id in tickets_out]
            backlog.reset_priority(tickets_out)
            #cursor.executemany('DELETE FROM backlog_ticket WHERE bklg_id=%s AND tkt_id=%s', tickets_out)
        #db.commit()

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['BACKLOGS_VIEW',
                ('BACKLOG_MODIFY', ['BACKLOG_VIEW']),
                ('BACKLOG_OWNER', ['BACKLOG_MODIFY']),
                ('BACKLOG_ADMIN', ['BACKLOG_OWNER'])]

    # ITemplateProvider methods
 
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('backlog', resource_filename(__name__, 'htdocs'))]

