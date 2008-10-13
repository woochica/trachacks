# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         ttadmin.py
# Purpose:      The ticket template Trac plugin handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

from trac.core import *
from trac.db import DatabaseManager
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor
from trac.web.chrome import *
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.perm import IPermissionRequestor

from trac.ticket import Milestone, Ticket, TicketSystem, ITicketManipulator

from trac.ticket.web_ui import NewticketModule

from webadmin.web_ui import IAdminPageProvider

from pkg_resources import resource_filename

import os
import pickle
import inspect
import time
import textwrap

from tickettemplate.model import schema, schema_version, TT_Template
from default_templates import DEFAULT_TEMPLATES

__all__ = ['TicketTemplateModule']

class TicketTemplateModule(Component):
    ticket_manipulators = ExtensionPoint(ITicketManipulator)
    
    implements(ITemplateProvider, 
               IAdminPageProvider, 
               INavigationContributor, 
               IRequestHandler, 
               IEnvironmentSetupParticipant, 
               IPermissionRequestor,
               )

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['TT_ADMIN']
        return actions

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        # Create the required tables
        db = self.env.get_db_cnx()
        connector, _ = DatabaseManager(self.env)._get_connector()
        cursor = db.cursor()
        for table in schema:
            for stmt in connector.to_sql(table):
                cursor.execute(stmt)

        # Insert a global version flag
        cursor.execute("INSERT INTO system (name,value) "
                       "VALUES ('tt_version',%s)", (schema_version,))

        # Create some default templates
        for tt_name, tt_text in DEFAULT_TEMPLATES:
            TT_Template.insert(self.env, tt_name, tt_text, 0)
        
        db.commit()

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='tt_version'")
        row = cursor.fetchone()
        if not row or int(row[0]) < schema_version:
            return True

    def upgrade_environment(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='tt_version'")
        row = cursor.fetchone()
        if not row:
            self.environment_created()
            current_version = 0
        else:    
            current_version = int(row[0])
            
        from tickettemplate import upgrades
        for version in range(current_version + 1, schema_version + 1):
            for function in upgrades.map.get(version):
                print textwrap.fill(inspect.getdoc(function))
                function(self.env, db)
                print 'Done.'
        cursor.execute("UPDATE system SET value=%s WHERE "
                       "name='tt_version'", (schema_version,))
        self.log.info('Upgraded tt tables from version %d to %d',
                      current_version, schema_version)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'newtplticket'

    def get_navigation_items(self, req):
        """ hijack the original Trac's 'New Ticket' handler to ticket template
        """
        if not req.perm.has_permission('TICKET_CREATE'):
            return
        yield ('mainnav', 'newticket', 
               html.A(u'New Ticket', href= req.href.newtplticket()))

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info in ['/newtplticket' ]


    def process_request(self, req):
        req.perm.assert_permission('TICKET_CREATE')
        
        if req.path_info == '/newtplticket':
            # call the original new ticket procedure
            template, content_type = NewticketModule(self.env).process_request(req)

            # get all templates for hdf
            tt_list = []
            indx = 0
            for tt_name in self._getTicketTypeNames():
                tt_item = {}
                tt_item["name"] = "description_%s" % indx
                tt_item["text"] = self._loadTemplateText(tt_name)
                tt_list.append(tt_item)
                indx += 1

            req.hdf['tt_list'] = tt_list
            
            # return the cs template
            return 'tt_newticket.cs', 0

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        self.env.log.info('get_admin_pages')

        if req.perm.has_permission('TRAC_ADMIN'):
            yield 'ticket', 'Ticket', 'tickettemplate', 'Ticket Template'


    def process_admin_request(self, req, cat, page, path_info):
        req.perm.assert_permission('TT_ADMIN')
        
        req.hdf['options'] = self._getTicketTypeNames()
        req.hdf['type'] = req.args.get('type')

        
        if req.args.has_key("id"):
            # after load history
            id = req.args.get("id")
            req.hdf['tt_text'] = self._loadTemplateTextById(id)
            req.hdf['type'] = self._getNameById(id)

        
        elif req.method == 'POST':

            # Load
            if req.args.get('loadtickettemplate'):
                tt_name = req.args.get('type')

                req.hdf['tt_text'] = self._loadTemplateText(tt_name)

            # Load history
            if req.args.get('loadhistory'):
                tt_name = req.args.get('type')
                
                req.hdf['tt_name'] = tt_name
                
                tt_history = []
                for id,modi_time,tt_name,tt_text in TT_Template.selectByName(self.env, tt_name):
                    history = {}
                    history["id"] = id
                    history["tt_name"] = tt_name
                    history["modi_time"] = self._formatTime(int(modi_time))
                    history["tt_text"] = tt_text
                    history["href"] = req.abs_href.admin(cat, page, {"id":id})
                    tt_history.append(history)
                
                req.hdf['tt_history'] = tt_history
                                
                return 'loadhistory.cs', None

            # Save
            elif req.args.get('savetickettemplate'):
                tt_text = req.args.get('description').replace('\r', '')
                tt_name = req.args.get('type')

                self._saveTemplateText(tt_name, tt_text)
                req.hdf['tt_text'] = tt_text
                
            # preview
            elif req.args.get('preview'):
                tt_text = req.args.get('description').replace('\r', '')
                tt_name = req.args.get('type')

                description_preview = self._previewTemplateText(tt_name, tt_text, req)
                req.hdf['tt_text'] = tt_text
                req.hdf['description_preview'] = description_preview

        return 'admin_tickettemplate.cs', None

    def _previewTemplateText(self, tt_name, tt_text, req):
        """ preview ticket template
        """
        db = self.env.get_db_cnx()        
        description_preview = wiki_to_html(tt_text, self.env, req, db)
        return description_preview
    

    # ITemplateProvider
    def get_templates_dirs(self):
        """
            Return the absolute path of the directory containing the provided
            templates
        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
            Return a list of directories with static resources (such as style
            sheets, images, etc.)
    
            Each item in the list must be a `(prefix, abspath)` tuple. The
            `prefix` part defines the path in the URL that requests to these
            resources are prefixed with.
            
            The `abspath` is the absolute path to the directory containing the
            resources on the local file system.
        """
        return [('tt', resource_filename(__name__, 'htdocs'))]
    
    # private methods

    def _loadTemplateText(self, tt_name):
        """ get tempate text from tt_dict.
            return tt_text if found in db
                or default tt_text if exists
                or empty string if default not exists.
        """
        tt_text = TT_Template.fetch(self.env, tt_name)
        if not tt_text:
            tt_text = TT_Template.fetch(self.env, "default")
        
        return tt_text

    def _getNameById(self, id):
        """ get tempate name from tt_dict.
        """
        tt_name = TT_Template.getNameById(self.env, id)
        
        return tt_name        
        
        
    def _loadTemplateTextById(self, id):
        """ get tempate text from tt_dict.
        """
        tt_text = TT_Template.fetchById(self.env, id)
        
        return tt_text        
        
    def _saveTemplateText(self, tt_name, tt_text):
        """ save ticket template text to db.
        """
        
        id = TT_Template.insert(self.env, tt_name, tt_text, time.time())
        return id

    def _getTicketTypeNames(self):
        """ get ticket type names
        """
        options = []

        ticket = Ticket(self.env)
        for field in ticket.fields:
            if field['name'] == 'type':
                options.extend(field['options'])

        options.extend(["default"])

        return options

    def _formatTime(self, modi_time):
        """
        """
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(modi_time))
