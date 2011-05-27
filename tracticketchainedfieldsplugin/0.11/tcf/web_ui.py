# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         web_ui.py
# Purpose:      The TracTicketChainedFields Trac plugin handler module
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
from trac.perm import IPermissionRequestor
from trac.web.api import RequestDone
from trac.web.api import ITemplateStreamFilter

from trac.ticket import Milestone, Ticket, TicketSystem, ITicketManipulator

from trac.admin import IAdminPanelProvider

from pkg_resources import resource_filename

import os
import inspect
import time
import textwrap
import simplejson

from model import schema, schema_version, TracTicketChainedFields_List

__all__ = ['TracTicketChainedFieldsModule']

class TracTicketChainedFieldsModule(Component):

    implements(ITemplateProvider,
               IAdminPanelProvider,
               IRequestHandler,
               IEnvironmentSetupParticipant,
               IPermissionRequestor,
               ITemplateStreamFilter,
               )

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['TCF_VIEW', 'TCF_ADMIN', ]
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
        cursor.execute("INSERT INTO system (name,value) VALUES ('tcf_version',%s)", (schema_version,))

        db.commit()

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='tcf_version'")
        row = cursor.fetchone()
        if not row or int(row[0]) < schema_version:
            return True

    def upgrade_environment(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='tcf_version'")
        row = cursor.fetchone()
        if not row:
            self.environment_created()
            current_version = 0
        else:
            current_version = int(row[0])

        from tcf import upgrades
        for version in range(current_version + 1, schema_version + 1):
            for function in upgrades.map.get(version):
                print textwrap.fill(inspect.getdoc(function))
                function(self.env, db)
                print 'Done.'
        cursor.execute("UPDATE system SET value=%s WHERE name='tcf_version'", (schema_version,))
        self.log.info('Upgraded TracTicketChainedFields tables from version %d to %d',
                      current_version, schema_version)


    # ITemplateProvider

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('tcf', resource_filename(__name__, 'htdocs'))]

    # ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        if filename == "ticket.html":
            # common js files
            add_script(req, 'tcf/tcf_ticket.js')
        return stream

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TCF_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', 'tcf_admin', u'Chained Fields')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TCF_ADMIN')

        data = {}
        
        if req.method == 'POST':
            if 'save' in req.args:
                tcf_define_json = req.args.get("tcf_define", "").strip()
                
                try:
                    tcf_define = simplejson.loads(tcf_define_json)
                except:
                    raise TracError(u"Format error, which should be JSON. Please back to last page and check the configuration.")
                
                TracTicketChainedFields_List.insert(self.env, tcf_define_json)
                
                req.redirect(req.abs_href.admin(cat, page))

        else:
            data["tcf_define"] = TracTicketChainedFields_List.get_tcf_define(self.env)
            return 'tcf_admin.html', data
            
    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/tcf')


    def process_request(self, req):
        hide_empty_fields = self.config.getbool("tcf", "hide_empty_fields", False)
        chained_fields = self.config.getlist("tcf", "chained_fields", [])
        
        if req.path_info.startswith('/tcf/query_tcf_define'):
            # handle XMLHTTPRequest
            result = {}
            result["status"] = "1"
            result["hide_empty_fields"] = hide_empty_fields
            result["chained_fields"] = chained_fields
            
            tcf_define = TracTicketChainedFields_List.get_tcf_define(self.env)
            try:
                result["tcf_define"] = simplejson.loads(tcf_define)
            except:
                pass
            
            if req.args.has_key("warning"):
                result["warning"] = "1"
            jsonstr = simplejson.dumps(result)
            self._sendResponse(req, jsonstr)
            
        elif req.path_info.startswith('/tcf/query_field_change'):
            result = {}
            result["status"] = "1"
            result["hide_empty_fields"] = hide_empty_fields
            
            trigger = req.args.get("trigger", "").lstrip("field-")
            if not trigger:
                result["status"] = "0"
                
            tcf_define = TracTicketChainedFields_List.get_tcf_define(self.env)
            try:
                tcf_define_target = simplejson.loads(tcf_define)
            except:
                pass
            
            target_field = ""
            target_options = []
            
            while True:
                if not tcf_define_target:
                    break
                elif trigger in tcf_define_target:
                    trigger_value = req.args.get("field-" + trigger, "")
                    
                    if not tcf_define_target[trigger].get(trigger_value):
                        try:
                            target_field = tcf_define_target[trigger].values()[0].keys()[0]
                        except:
                            pass
                        tcf_define_target = {}
                    else:
                        tcf_define_target = tcf_define_target[trigger].get(trigger_value)
                        target_field = tcf_define_target.keys()[0]
                    break
                else:
                    field = tcf_define_target.keys()[0]
                    field_value = req.args.get("field-" + field, "")
                    
                    if not field_value:
                        tcf_define_target = tcf_define_target.values()[0].values()[0]
                    else:
                        tcf_define_target = tcf_define_target.values()[0].get(field_value, {})
                        
            targets = []
            if tcf_define_target:
                for k, v in tcf_define_target.items():
                    target_field = k
                    target_options = [target_option for target_option in v.keys() if target_option]
                    target_options.sort(cmp=lambda x,y: cmp(x.lower(), y.lower()))
                    
                    targets.append({
                        "target_field": target_field, 
                        "target_options": target_options, 
                    })
            
            result["targets"] = targets
            
            if req.args.has_key("warning"):
                result["warning"] = "1"
            jsonstr = simplejson.dumps(result)
            self._sendResponse(req, jsonstr)

    # internal methods
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

