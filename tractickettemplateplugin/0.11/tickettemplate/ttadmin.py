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

from trac.web.api import RequestDone

from trac.web.api import ITemplateStreamFilter

from trac.ticket import Milestone, Ticket, TicketSystem, ITicketManipulator
from trac.web.chrome import add_ctxtnav, add_link, add_script, add_stylesheet, \
                            Chrome

from trac.ticket.web_ui import TicketModule

from trac.admin import IAdminPanelProvider

from trac.util.compat import partial

from genshi.filters.transform import Transformer

from pkg_resources import resource_filename

import sys
import os
import pickle
import inspect
import time
import textwrap
import urllib

if sys.version_info[0] == 2 and sys.version_info[1] > 5:
    import json
else:
    import simplejson as json

from tickettemplate.model import schema, schema_version, TT_Template

from utils import *

from i18n_domain import gettext, _, tag_, N_, add_domain

__all__ = ['TicketTemplateModule']

class TicketTemplateModule(Component):
    
    implements(ITemplateProvider, 
               IAdminPanelProvider, 
               IEnvironmentSetupParticipant, 
               IPermissionRequestor,
               ITemplateStreamFilter,
               IRequestHandler, 
               )

    def __init__(self):
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['TT_USER', ('TT_ADMIN', ['TT_USER'])]
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
        now = int(time.time())
        from default_templates import DEFAULT_TEMPLATES
        for tt_name, tt_value in DEFAULT_TEMPLATES:
            record = [
                now,
                SYSTEM_USER,
                tt_name,
                "description",
                tt_value,
                ]
            TT_Template.insert(self.env, record)
        
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
    def get_admin_panels(self, req):
        if 'TT_ADMIN' in req.perm:
            yield ('ticket', _('Ticket System'), 'tickettemplate', _('Ticket Template'))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TT_ADMIN')

        data = {
            "gettext": gettext,
            "_": _,
            "tag_": tag_,
            "N_": N_,
        }
        
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
        return req.path_info.startswith('/tt')

    def process_request(self, req):
        req.perm.assert_permission('TICKET_CREATE')
        data = {
            "gettext": gettext,
            "_": _,
            "tag_": tag_,
            "N_": N_,
        }
        
        if req.path_info.startswith('/tt/query'):
            # handle XMLHTTPRequest
            data["req_args"] = req.args
                
            data.update({"tt_user": req.authname})
            result = TT_Template.fetchAll(self.env, data)
            result["status"] = "1"
            result["field_list"] = self._getFieldList()
            if self.config.getbool("tickettemplate", "enable_custom", True) and \
                'TT_USER' in req.perm:
                result["enable_custom"] = True
            else:
                result["enable_custom"] = False
            if req.args.has_key("warning"):
                result["warning"] = "1"
            jsonstr = json.dumps(result)
            self._sendResponse(req, jsonstr)

        # tt_custom save
        elif req.path_info.startswith('/tt/custom_save'):
            tt_name, custom_template = self._handleCustomSave(req);
            result = {}
            result["status"] = "1"
            result["tt_name"] = tt_name
            result["new_template"] = custom_template
            jsonstr = json.dumps(result)
            self._sendResponse(req, jsonstr)

        # tt_custom delete
        elif req.path_info.startswith('/tt/custom_delete'):
            tt_name = self._handleCustomDelete(req);
            result = {}
            result["status"] = "1"
            result["tt_name"] = tt_name
            jsonstr = json.dumps(result)
            self._sendResponse(req, jsonstr)

        elif req.path_info.startswith('/tt/edit_buffer_save'):
            tt_name, custom_template = self._handleCustomSave(req);
            result = {}
            result["status"] = "1"
            result["tt_name"] = tt_name
            result["new_template"] = custom_template
            jsonstr = json.dumps(result)
            self._sendResponse(req, jsonstr)
        elif req.path_info.startswith('/tt/tt_newticket.js'):
            filename = resource_filename(__name__, 'templates/tt_newticket.js')
            chrome = Chrome(self.env)
            message = chrome.render_template(req, filename, data, 'text/plain')
            
            req.send_response(200)
            req.send_header('Cache-control', 'no-cache')
            req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
            req.send_header('Content-Type', 'text/x-javascript')
            req.send_header('Content-Length', len(isinstance(message, unicode) and message.encode("utf-8") or message))
            req.end_headers()

            if req.method != 'HEAD':
                req.write(message)
            raise RequestDone
            
    # ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        if filename == "ticket.html" and req.path_info.startswith('/newticket'):
            # common js files
            add_script(req, 'tt/json2.js')
            
            stream = stream | Transformer('body').append(
                tag.script(type="text/javascript", 
                src=req.href("tt", "tt_newticket.js"))()
            )

        return stream
    
    # internal methods
    def _handleCustomDelete(self, req):
        """ delete custom template
        """
        jsonstr = urllib.unquote(req.read())
        custom_data = json.loads(jsonstr)
        tt_name = custom_data.get("tt_name")
        if not tt_name:
            return

        tt_user = req.authname

        # delete same custom template if exist
        delete_data = {
            "tt_user": tt_user,
            "tt_name": tt_name,
            }
        TT_Template.deleteCustom(self.env, delete_data)
        return tt_name

    def _handleCustomSave(self, req):
        """ save custom template
        """
        jsonstr = urllib.unquote(req.read())
        custom_data = json.loads(jsonstr)
        tt_name = custom_data.get("tt_name")
        custom_template = custom_data.get("custom_template")
        if not tt_name or not custom_template:
            return tt_name, custom_template

        now = int(time.time())
        tt_user = req.authname

        # delete same custom template if exist
        delete_data = {
            "tt_user": tt_user,
            "tt_name": tt_name,
            }
        TT_Template.deleteCustom(self.env, delete_data)

        # save custom template
        field_list = self._getFieldList()
        for tt_field in field_list:
            tt_value = custom_template.get(tt_field)

            if tt_value is not None:
                record = [
                    now,
                    tt_user,
                    tt_name,
                    tt_field,
                    tt_value,
                    ]
                TT_Template.insert(self.env, record)

        return tt_name, custom_template

    def _getFieldList(self):
        """ Get available fields
            return:
                ["summary", "description", ...]
        """
        field_list = self.config.getlist("tickettemplate", "field_list", [])
        field_list = [field.lower() for field in field_list]
        if "description" not in field_list:
            field_list.append("description")
        return field_list

    def _getTTFields(self, tt_user, tt_name):
        """
            Get all fields values
            return:
                {
                    "summary": {"field_type":"text", "field_value": "abc"},
                    "description": {"field_type":"textarea", "field_value": "xyz"},
                }

        """
        result = {}

        # init result
        field_list = self._getFieldList()
        for field in field_list:
            result[field] = ""

        # update from db
        data = {
            "tt_user": tt_user,
            "tt_name": tt_name,
            }
        field_value_mapping = TT_Template.fetchCurrent(self.env, data)
        for k, v in field_value_mapping.items():
            if k in field_list:
                result[k] = v

        for field in field_list:
            field_type = self.config.get("tickettemplate", field + ".type", "text")
            field_value = field_value_mapping.get(field)
            field_detail = {"field_type":field_type, "field_value": field_value}
            result[field] = field_detail

        return result
        
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

    def _sendResponse(self, req, message):
        """ send response and stop request handling
        """
        req.send_response(200)
        req.send_header('Cache-control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', 'text/plain' + ';charset=utf-8')
        req.send_header('Content-Length', len(isinstance(message, unicode) and message.encode("utf-8") or message))
        req.end_headers()

        if req.method != 'HEAD':
            req.write(message)
        raise RequestDone


    def _saveTemplateText(self, tt_name, tt_text):
        """ save ticket template text to db.
        """
        id = TT_Template.insert(self.env, (int(time.time()), "SYSTEM", tt_name, "description", tt_text))
        return id

        
    def _getTicketTypeNames(self):
        """ get ticket type names
            return:
                ["defect", "enhancement", ..., "default"]
        """
        options = []

        ticket = Ticket(self.env)
        for field in ticket.fields:
            if field['name'] == 'type':
                options.extend(field['options'])

        options.extend(["default"])

        return options
        
