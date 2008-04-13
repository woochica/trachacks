# Copyright (C) 2008 Tim Coulter
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301
# USA

"""
TrashTalk Plugin
author: Tim Coulter <tim@timothyjcoulter.com>
version: 0.1

TrashTalk tracks and lists URLs from external websites that link to
each ticket. Using TrashTalk, developers can get a better sense of
how their bugs affect the community by paying attention to "who's talking" 
about each ticket. 

Some functions below were legally pilferred from the tracpasteplugin:
http://www.trac-hacks.org/wiki/TracPastePlugind
"""

import re

from genshi.builder import tag

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.db import Table, Column, Index
from trac.resource import ResourceNotFound
from trac.web.api import *
from trac.ticket import Ticket

class TrashTalkBackend(Component):
    implements()

class TrashTalkPlugin(Component):
    implements(IRequestFilter, IEnvironmentSetupParticipant)

    SCHEMA = [
        Table('incoming_links', key='id')[
            Column('id', auto_increment=True),
            Column('ticket'),                  # The id of the ticket that has been linked to.
            Column('external_url'),            # The url linking to the ticket.
            Column('count'),                   # The number of times the external url referred to the ticket.
            Column('first', type='int'),       # The first time the external_url linked to the ticket.
            Column('most_recent', type='int')  # The most recent time the external_url link to the ticket.
        ]
    ]

    TICKET_URI_PATTERN = re.compile("^/ticket/(\d+)(?:$|.*$)", re.VERBOSE)

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self._upgrade_db(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute('select count(*) from trashtalk')
            cursor.fetchone()
            return False
        except:
            db.rollback()
            return True

    def upgrade_environment(self, db):
        self._upgrade_db(db)


    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if self._is_external(req) and self._is_ticket(req):
            self._talk_about(req)
        return handler
    
    # for ClearSilver templates
    def post_process_request(self, req, template, content_type):
        return (template, content_type)
    
    # for Genshi templates
    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)
    
    # Private methods
    def _talk_about(self, req):
        
        ticket_id = int(self.TICKET_URI_PATTERN.findall(req.path_info)[0])
        ticket = Ticket(self.env, ticket_id)
        
        ticket.save_changes("tcoulter", req.get_header("referer"))
        
        print "::: " + req.get_header("referer")
        print "--> " + req.abs_href() + req.path_info
        
        
    def _is_external(self, req):
        referer = req.get_header("referer")
        return referer and not referer.startswith(req.abs_href())
    
    def _is_ticket(self, req):
        return len(self.TICKET_URI_PATTERN.findall(req.path_info)) > 0
    
    def _upgrade_db(self, db):
        try:
            try:
                from trac.db import DatabaseManager
                db_backend, _ = DatabaseManager(self.env)._get_connector()
            except ImportError:
                db_backend = self.env.get_db_cnx()

            cursor = db.cursor()
            for table in self.SCHEMA:
                for stmt in db_backend.to_sql(table):
                    self.env.log.debug(stmt)
                    cursor.execute(stmt)
            db.commit()
        except Exception, e:
            db.rollback()
            self.env.log.error(e, exc_info=1)
            raise TracError(str(e))
    
