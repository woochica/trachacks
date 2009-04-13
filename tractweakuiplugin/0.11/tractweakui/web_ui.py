# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         web_ui.py
# Purpose:      The TracTweakUI Trac plugin handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

from trac.core import *
from trac.db import DatabaseManager
from trac.web.chrome import *
from trac.util.html import html

from trac.web import IRequestHandler
from trac.web.api import RequestDone, HTTPException
from trac.web.api import ITemplateStreamFilter
from trac.admin import IAdminPanelProvider
from trac.perm import IPermissionRequestor
from trac.web.chrome import add_stylesheet, add_script
from trac.util.text import to_unicode

from pkg_resources import resource_filename
from genshi.filters.transform import Transformer

import sys, os
import re
import time
import inspect
import textwrap

from utils import *

from model import schema, schema_version, TracTweakUIModel

__all__ = ['TracTweakUIModule']

class TracTweakUIModule(Component):

    implements(ITemplateProvider,
               IRequestHandler, 
               ITemplateStreamFilter,
               IAdminPanelProvider, 
               IEnvironmentSetupParticipant, 
               IPermissionRequestor,
               #INavigationContributor,
               )

    # ITemplateProvider

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('tractweakui', resource_filename(__name__, 'htdocs'))]

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['TRACTWEAKUI_VIEW', 'TRACTWEAKUI_ADMIN', ]
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
        cursor.execute("INSERT INTO system (name,value) VALUES ('tractweakui_version',%s)", (schema_version,))

        db.commit()

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='tractweakui_version'")
        row = cursor.fetchone()
        if not row or int(row[0]) < schema_version:
            return True

    def upgrade_environment(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='tractweakui_version'")
        row = cursor.fetchone()
        if not row:
            self.environment_created()
            current_version = 0
        else:    
            current_version = int(row[0])
            
        from tractweakui import upgrades
        for version in range(current_version + 1, schema_version + 1):
            for function in upgrades.map.get(version):
                print textwrap.fill(inspect.getdoc(function))
                function(self.env, db)
                print 'Done.'
        cursor.execute("UPDATE system SET value=%s WHERE name='tractweakui_version'", (schema_version,))
        self.log.info('Upgraded TracTweakUI tables from version %d to %d',
                      current_version, schema_version)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRACTWEAKUI_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', 'tractweakui_admin', 'TracTweakUI Admin')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TRACTWEAKUI_ADMIN')

        data = {}
        data["page"] = page
        data["encode_url"] = encode_url
        #print cat, page, path_info

        # Analyze url
        action = ""
        if path_info:
            try:
                action, args = path_info.split('?', 1)
                action = action.strip("/")
            except:
                action = path_info.strip("/")
                args = None

        if action:
            if action == "edit_path_pattern":
                # edit path_pattern
                if req.method == 'POST':
                    # TODO
                    if 'save' in req.args:
                        # save filter
                        path_pattern = req.args.get("path_pattern", "").strip()
                        path_pattern_orig = req.args.get("path_pattern_orig", "").strip()
                        self._save_path_pattern(req)
                        
                        req.redirect(req.abs_href.admin(cat, page))

                    elif 'delete' in req.args:
                        # delete filter
                        path_pattern = req.args.get("path_pattern", "").strip()
                        self._del_path_pattern(req)
                        req.redirect(req.abs_href.admin(cat, page))

                else:
                    # list filters
                    path_pattern = req.args.get("path_pattern", "").strip()
                    data["filter_names"] = self._get_filters()
                    data["path_pattern"] = req.args.get("path_pattern", "").strip()
                    #print data
                    return 'tractweakui_admin_list_filter.html', data

            elif action.startswith("edit_filter_script"):
                # edit script
                if req.method == 'POST':
                    if 'save' in req.args:
                        # save filter
                        self._save_tweak_script(req)
                        #req.redirect(req.abs_href.admin(cat, page, path_info))
                        path_pattern = req.args.get("path_pattern", "").strip()
                        data["filter_names"] = self._get_filters()
                        data["path_pattern"] = req.args.get("path_pattern", "").strip()
                        #print data
                        return 'tractweakui_admin_list_filter.html', data

                    elif 'load_default' in req.args:
                        # load_default js script
                        data['path_pattern'] = req.args.get("path_pattern", "").strip()
                        data['filter_name'] = req.args.get("filter_name", "").strip()
                        data['tweak_script'] = self._load_default_script(req)
                        #print data
                        return 'tractweakui_admin_edit_filter.html', data

                else:
                    # display filter details
                    path_pattern = req.args.get("path_pattern", "").strip()
                    filter_name = req.args.get("filter_name", "").strip()
                    tweak_script = TracTweakUIModel.get_tweak_script(self.env, path_pattern, filter_name)
                    data['tweak_script'] = tweak_script
                    data['path_pattern'] = path_pattern
                    data['filter_name'] = filter_name
                    return 'tractweakui_admin_edit_filter.html', data

            elif action == "add_path_pattern":
                # add path pattern
                if req.method == 'POST':
                    if 'add' in req.args:
                        self._add_path_pattern(req)
                        req.redirect(req.abs_href.admin(cat, page))
        else:
            # list all path patterns
            data["path_patterns"] = TracTweakUIModel.get_path_patterns(self.env)
            return 'tractweakui_admin_list_path.html', data

    # ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        # get all path patterns
        path_patterns = TracTweakUIModel.get_path_patterns(self.env)
        # try to match pattern
        for path_pattern in path_patterns:
            if re.match(path_pattern, req.path_info):
                break
        else:
            return stream

        filter_names = TracTweakUIModel.get_path_filters(self.env, path_pattern)
        for filter_name in filter_names:
            stream = self._apply_filter(req, stream, path_pattern, filter_name)
        stream = stream | Transformer('head').append(
            tag.script(type="text/javascript", 
            src= req.base_path + "/tractweakui/tweakui_js/" + urllib.quote(path_pattern, "") + ".js")()
            )

        return stream

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/tractweakui/tweakui_js')

    def process_request(self, req):
        filter_base_path = os.path.normpath(os.path.join(self.env.path, "htdocs", "tractweakui"))
        if not os.path.exists(filter_base_path):
            return self._send_response(req, "")

        tweakui_js_path = '/tractweakui/tweakui_js'
        if req.path_info.startswith(tweakui_js_path):
            path_pattern = urllib.unquote(req.path_info[len(tweakui_js_path) + 1 : -3])
            js_files = TracTweakUIModel.get_path_scripts(self.env, path_pattern)
            if js_files:
                script = ";\n".join(js_files)
            else:
                script = ""
            self._send_response(req, script, {'Content-Type': 'text/x-javascript'})

    # internal methods
    def _apply_filter(self, req, stream, path_pattern, filter_name):
        # get filter path
        filter_path = os.path.normpath(os.path.join(self.env.path, "htdocs", "tractweakui", filter_name))
        if not os.path.exists(filter_path):
            return stream

        css_files = self._find_filter_files(filter_path, "css")
        js_files = self._find_filter_files(filter_path, "js")

        for css_file in css_files:
            stream = self._add_css(req, stream, filter_name, css_file)
        for js_file in js_files:
            if js_file != "__template__.js":
                stream = self._add_js(req, stream, filter_name, js_file)
        return stream

    def _find_filter_files(self, filter_path, file_type):
        if not os.path.exists(filter_path):
            return []
        return [file for file in os.listdir(filter_path) if file.endswith(file_type)]

    def _get_filters(self):
        filter_base_path = os.path.normpath(os.path.join(self.env.path, "htdocs", "tractweakui"))
        if not os.path.exists(filter_base_path):
            return []

        return [file for file in os.listdir(filter_base_path)]

    def _add_js(self, req, stream, filter_name, js_file):
        return stream | Transformer('head').append(
            tag.script(type="text/javascript", 
            src=req.href.chrome("site/tractweakui/" + filter_name, js_file))()
            )

    def _add_css(self, req, stream, filter_name, css_file):
        return stream | Transformer('head').append(
                tag.link(type="text/css", 
                rel="stylesheet", 
                href=req.href.chrome("site/tractweakui/" + filter_name, css_file))()
            )

    def _send_response(self, req, message, headers = {}):
        """
        """
        req.send_response(200)
        req.send_header('Cache-control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', 'text/plain')
        #req.send_header('Content-Length', len(message))

        for k, v in headers.items():
            req.send_header(k, v)

        req.end_headers()

        if req.method != 'HEAD':
            req.write(message)
        raise RequestDone

    def _add_path_pattern(self, req):
        """ add filter
        """
        path_pattern = req.args.get("path_pattern", "").strip()

        # add to db
        TracTweakUIModel.insert_path_pattern(self.env, path_pattern)

    def _save_path_pattern(self, req):
        """ add filter
        """
        path_pattern = req.args.get("path_pattern", "").strip()
        path_pattern_orig = req.args.get("path_pattern_orig", "").strip()

        # add to db
        TracTweakUIModel.save_path_pattern(self.env, path_pattern, path_pattern_orig)

    def _del_path_pattern(self, req):
        """ del filter
        """
        path_pattern = req.args.get("path_pattern", "").strip()

        # add to db
        TracTweakUIModel.del_path_pattern(self.env, path_pattern)

    def _save_tweak_script(self, req):
        """ save tweak_script
        """
        filter_name = req.args.get("filter_name", "").strip()
        path_pattern = req.args.get("path_pattern", "").strip()
        tweak_script = req.args.get("tweak_script", "").strip()

        # add to db
        TracTweakUIModel.save_tweak_script(self.env, path_pattern, filter_name, tweak_script)

    def _load_default_script(self, req):
        """ 
        """
        filter_name = req.args.get("filter_name", "").strip()
        path_pattern = req.args.get("path_pattern", "").strip()

        template_path = os.path.normpath(os.path.join(self.env.path, "htdocs", "tractweakui", filter_name, "__template__.js"))
        if not os.path.exists(template_path):
            return ""
        
        try:
            return to_unicode(open(template_path).read())
        except Exception, e:
            self.log.error("Load js template failed.", exc_info=True)
            return ""

