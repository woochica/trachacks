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

Some methods below were legally pilferred from the tracpasteplugin:
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
from trac.util.datefmt import utc, to_timestamp
from datetime import datetime

def sql_escape_percent(sql):
    import re
    return re.sub("'((?:[^']|(?:''))*)'", lambda m: m.group(0).replace('%', '%%'), sql)

def get_incoming_links_for_ticket(env, ticket, db=None):
    """Return all incoming links for the given ticket."""
    cursor = (db or env.get_db_cnx()).cursor()
    cursor.execute('select * from incoming_links where id=%s order by first desc', (ticket,))
    result = []
    for row in cursor:
        result.append({
            'id':                   row[0],
            'ticket':               row[1],
            'external_url':         row[2],
            'click_count':          row[3],
            'first':                datetime.fromtimestamp(row[4], utc),
            'most_recent':          datetime.fromtimestamp(row[5], utc)
        })
    return result

class TrashTalkPlugin(Component):
    implements(IRequestFilter, IEnvironmentSetupParticipant)

    SCHEMA = [
        Table('incoming_links', key='id')[
            Column('id', auto_increment=True),
            Column('ticket'),                  # The id of the ticket that has been linked to.
            Column('external_url'),            # The url linking to the ticket.
            Column('click_count'),             # The number of times the external url has been clicked on.
            Column('first', type='int'),       # The first time the external_url linked to the ticket.
            Column('most_recent', type='int')  # The most recent time the external_url link to the ticket.
        ]
    ]
    
    SCHEMA_LOOKUP = {
        'id':           0,
        'ticket':       1,
        'external_url': 2,
        'click_count':  3,
        'first':        4,
        'most_recent':  5
    }

    TICKET_URI_PATTERN = re.compile("^/ticket/(\d+)(?:$|.*$)", re.VERBOSE)

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self._upgrade_db(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute('select count(*) from incoming_links')
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
        
        # Eventually, some kind of model should be created for incoming links.
        # Right now though, for a first implementation, this will suffice.
        
        ticket = int(self.TICKET_URI_PATTERN.findall(req.path_info)[0])
        external_url = req.get_header("referer")
        click_count = 1
        most_recent = datetime.now(utc)
        first = most_recent
        
        # Let's get a database connection.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        # See if the current link is already in the database for this ticket.
        cursor.execute('select * from incoming_links where ticket = %s and external_url = %s limit 1', (ticket, external_url))
        
        row = cursor.fetchone()
        
        # Have we recorded the external_url for this ticket before?
        if row:
            # Yes. Let's update the click count and the most_recent timestamp.
            id = row[self.SCHEMA_LOOKUP['id']]
            click_count = int(row[self.SCHEMA_LOOKUP['click_count']]) + 1
            
            cursor.execute('update incoming_links set click_count = %s, most_recent = %s where id = %s', (click_count, most_recent, id)) 
        else:
            # No. Let's create a new row.
            cursor.execute('insert into incoming_links (ticket, external_url, click_count, first, most_recent) values (%s, %s, %s, %s, %s)',
                           (ticket, external_url, click_count, first, most_recent))

        # Commit changes...
        db.commit()
        
        
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
    
