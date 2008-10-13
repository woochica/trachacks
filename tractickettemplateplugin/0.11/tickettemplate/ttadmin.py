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
from trac.web.chrome import *
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.perm import IPermissionRequestor
from trac.web import IRequestHandler

from trac.web.api import ITemplateStreamFilter

from trac.ticket import Milestone, Ticket, TicketSystem, ITicketManipulator

from trac.ticket.web_ui import TicketModule

from trac.admin import IAdminPanelProvider

from trac.util.translation import _

from genshi.filters.transform import Transformer

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
               IAdminPanelProvider, 
               IEnvironmentSetupParticipant, 
               IPermissionRequestor,
               ITemplateStreamFilter,
               IRequestHandler, 
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

    # IAdminPanelProvider methods
    _type = 'tickettemplate'
    _label = ('Ticket Template', 'Ticket Template')

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', self._type, self._label[1])

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TT_ADMIN')

        data = {}
        
        data['options'] = self._getTicketTypeNames()
        data['type'] = req.args.get('type')

        
        if req.args.has_key("id"):
            # after load history
            id = req.args.get("id")
            data['tt_text'] = self._loadTemplateTextById(id)
            data['type'] = self._getNameById(id)

        
        elif req.method == 'POST':

            # Load
            if req.args.get('loadtickettemplate'):
                tt_name = req.args.get('type')

                data['tt_text'] = self._loadTemplateText(tt_name)

            # Load history
            if req.args.get('loadhistory'):
                tt_name = req.args.get('type')
                
                data['tt_name'] = tt_name
                
                tt_history = []
                for id,modi_time,tt_name,tt_text in TT_Template.selectByName(self.env, tt_name):
                    history = {}
                    history["id"] = id
                    history["tt_name"] = tt_name
                    history["modi_time"] = self._formatTime(int(modi_time))
                    history["tt_text"] = tt_text
                    history["href"] = req.abs_href.admin(cat, page, {"id":id})
                    tt_history.append(history)
                
                data['tt_history'] = tt_history
                                
                return 'loadhistory.html', data

            # Save
            elif req.args.get('savetickettemplate'):
                tt_text = req.args.get('description').replace('\r', '')
                tt_name = req.args.get('type')

                self._saveTemplateText(tt_name, tt_text)
                data['tt_text'] = tt_text
                
            # preview
            elif req.args.get('preview'):
                tt_text = req.args.get('description').replace('\r', '')
                tt_name = req.args.get('type')

                description_preview = self._previewTemplateText(tt_name, tt_text, req)
                data['tt_text'] = tt_text
                data['description_preview'] = description_preview

        return 'admin_tickettemplate.html', data


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

    # IRequestHandler methods

    def match_request(self, req):
        #return req.path_info.startswith('/newticket')
        return req.path_info.startswith('/tt_custom')

    def process_request(self, req):
        req.perm.assert_permission('TICKET_CREATE')

        # tt_custom
        if req.path_info.startswith('/tt_custom') and req.method == "POST":
            if req.args.get("tt_custom_save"):
                tt_text = req.args.get("tt_custom_textarea")
                tt_name = req.args.get("tt_custom_name")
                if tt_name and tt_text:
                    TT_Template.saveCustom(self.env, req.authname, tt_name, tt_text)

            elif req.args.get("tt_custom_delete"):
                tt_custom_select = req.args.get("tt_custom_select")
                TT_Template.deleteCustom(self.env, req.authname, tt_custom_select)

            req.redirect(req.base_path + "/newticket")


    ## ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        if filename == "ticket.html" and req.path_info == '/newticket' and not req.args.get("preview"):
            # tt.js
            stream = stream | Transformer('body').append(
                tag.script(type="text/javascript", 
                src=req.href.chrome("tt", "tt.js"))()
            )

            # get all templates
            all_textarea = tag.textarea()
            indx = 0
            for tt_name in self._getTicketTypeNames():
                all_textarea += tag.textarea(id="description_%s" % indx)(Markup(self._loadTemplateText(tt_name)))
                indx += 1

            stream = stream | Transformer('body').after(tag.div(id="tt_div", style=
                "z-index:-99; visibility:hidden; "
                "position:static; top:-1000; right:-1000; ")) \
                .end().select('//*[@id="tt_div"]') \
                .prepend(all_textarea)

            # short circut if not enable_custom
            if not self.config.get("tickettemplate", "enable_custom"):
                return stream

            # custom

            # select
            selected_name = None

            # get tt_custom_names
            rows = TT_Template.getCustomTemplate(self.env, req.authname)
            tt_custom_names = [row[0] for row in rows]
            # add one empty item
            tt_custom_names.append("")

            tt_custom_mapping = {}
            for row in rows:
                tt_custom_mapping[row[0]] = row[1]

            # get all templates
            all_textarea = tag.textarea(id="tt_custom_textarea", name="tt_custom_textarea")
            indx = 0
            for tt_name in tt_custom_names:
                all_textarea += tag.textarea(id="tt_custom_%s" % indx)(Markup(tt_custom_mapping.get(tt_name, "")))
                indx += 1

            tt_custom = tag.form(
                tag.div(
                    tag.fieldset(
                        tag.legend("My Templates"),
                            tag.select([tag.option(x, selected=None) for x in tt_custom_names],
                                id="tt_custom_select", name="tt_custom_select", style="width:10em;"
                                ), 
                            tag.br(),
                            tag.input(type='hidden', name="tt_custom_name", id="tt_custom_name"), 
                            tag.br(),
                            tag.input(type='submit', name="tt_custom_save", id="tt_custom_save", value='create'), 
                            tag.input(type='submit', name="tt_custom_delete", value='delete'), 
                            tag.div(
                                all_textarea,
                                style='z-index: -99; visibility: hidden; position: absolute;'),
                            ),
                    id="tt_custom", 
                    style="position:static; "),
                id="tt_custom_form",
                name="tt_custom_form",
                method="post",
                action="tt_custom",
                style=" clear: right; float: right; margin: 10em 0 4em; width: 200px; ",
                )

            stream = stream | Transformer('//div[@id="content"]').before(tt_custom)
            #select('items/item[@status="closed" and  (@resolution="invalid" or not(@resolution))]/summary/text()')


        return stream
    
    # private methods
    def _previewTemplateText(self, tt_name, tt_text, req):
        """ preview ticket template
        """
        db = self.env.get_db_cnx()        
        description_preview = wiki_to_html(tt_text, self.env, req, db)
        return description_preview
    
    def _getCustomTemplates(self, req):
        """
        """
        return TT_Template.getCustomTemplate(self.env, req.authname)

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
