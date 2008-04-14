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
http://www.trac-hacks.org/wiki/TracPastePlugin
"""

import re

from genshi.core import Markup
from genshi.builder import tag
from genshi.filters.transform import Transformer

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.db import Table, Column, Index
from trac.resource import ResourceNotFound
from trac.ticket import Ticket
from trac.util.datefmt import utc, to_timestamp
from datetime import datetime

from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet

class TrashTalkPlugin(Component):
    implements(IEnvironmentSetupParticipant, ITemplateStreamFilter, ITemplateProvider, IRequestFilter)

    SCHEMA = [
        Table('incoming_links', key='id')[
            Column('id', auto_increment=True),
            Column('ticket'),                  # The id of the ticket that has been linked to.
            Column('external_url'),            # The url linking to the ticket.
            Column('click_count', type='int'), # The number of times the external url has been clicked on.
            Column('first', type='int'),       # The first time the external_url linked to the ticket.
            Column('most_recent', type='int')  # The most recent time the external_url linked to the ticket.
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

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        
        if self._is_ticket(req):
            
            if self._is_external(req):
                self._talk_about(req)
            
            ticket = self._get_ticket_from_request(req)
            links = self._get_incoming_links_for_ticket(ticket)
            
            if len(links) != 0:
        
                ticket = self._get_ticket_from_request(req)
                
                div = tag.div(id="trashtalk")
    
                for link in links:
                    a = tag.a(href=link['external_url'])
                    a(link['external_url'])
                    div(a)
                    div(" (%s)" % link['click_count'])
                    div(tag.br)
                
                stream |= Transformer('//div[@id="ticket"]').after(div).after(tag.h2("Incoming Links"))

        return stream
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    # for ClearSilver templates
    def post_process_request(self, req, template, content_type):
        return (template, content_type)

    # for Genshi templates
    def post_process_request(self, req, template, data, content_type):
        #if self._is_ticket(req):
        add_stylesheet(req, 'trashtalk/trashtalk.css')

        return (template, data, content_type)
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('trashtalk', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        #from pkg_resources import resource_filename
        #return [resource_filename(__name__, 'templates')]
        return []
    
    # Private methods
    def _talk_about(self, req):
        
        # Eventually, some kind of model should be created for incoming links.
        # Right now though, for a first implementation, this will suffice.
        
        ticket = self._get_ticket_from_request(req)
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
    
    def _get_ticket_from_request(self, req):
        return int(self.TICKET_URI_PATTERN.findall(req.path_info)[0])
    
    def _get_incoming_links_for_ticket(self, ticket):
        # Let's get a database connection.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('select * from incoming_links where ticket=%s order by first desc', str(ticket))
        
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                'id':                   row[self.SCHEMA_LOOKUP['id']],
                'ticket':               row[self.SCHEMA_LOOKUP['ticket']],
                'external_url':         row[self.SCHEMA_LOOKUP['external_url']],
                'click_count':          row[self.SCHEMA_LOOKUP['click_count']],
                'first':                row[self.SCHEMA_LOOKUP['first']],
                'most_recent':          row[self.SCHEMA_LOOKUP['most_recent']]
            })
        return result
    
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
        

    
