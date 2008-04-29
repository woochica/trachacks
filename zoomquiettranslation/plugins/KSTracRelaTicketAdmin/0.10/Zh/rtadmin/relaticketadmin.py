# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         rtadmin.py
# Purpose:      The relaticket admin Trac plugin handler module
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
from trac.web.api import RequestDone

from trac.ticket import Milestone, Ticket, TicketSystem

from trac.ticket.web_ui import NewticketModule

from webadmin.web_ui import IAdminPageProvider

from pkg_resources import resource_filename

import os
import pickle
import inspect
import time
import textwrap

from model import schema, schema_version, RT_Template

__all__ = ['RelaTicketAdminModule']

class RelaTicketAdminModule(Component):
    
    implements(ITemplateProvider, 
               IAdminPageProvider, 
               INavigationContributor, 
               IRequestHandler, 
               IEnvironmentSetupParticipant, 
               IPermissionRequestor,
               )

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['RT_ADMIN']
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
                       "VALUES ('rtadmin_version',%s)", (schema_version,))

        db.commit()

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='rtadmin_version'")
        row = cursor.fetchone()
        if not row or int(row[0]) < schema_version:
            return True

    def upgrade_environment(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='rtadmin_version'")
        row = cursor.fetchone()
        if not row:
            self.environment_created()
            current_version = 0
        else:    
            current_version = int(row[0])
            
        from rtadmin import upgrades
        for version in range(current_version + 1, schema_version + 1):
            for function in upgrades.map.get(version):
                print textwrap.fill(inspect.getdoc(function))
                function(self.env, db)
                print 'Done.'
        cursor.execute("UPDATE system SET value=%s WHERE "
                       "name='rtadmin_version'", (schema_version,))
        self.log.info('Upgraded rtadmin tables from version %d to %d',
                      current_version, schema_version)

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        self.env.log.info('get_admin_pages')

        if req.perm.has_permission('RT_ADMIN'):
            yield 'ticket', 'Ticket', 'rtadmin', 'RelaTicket Admin'


    def process_admin_request(self, req, cat, page, path_info):
        req.perm.assert_permission('RT_ADMIN')

        if req.method == 'POST':
            if req.args.get('save') and req.args.get('sel'):

                # empty table first
                RT_Template.deleteAll(self.env)
                
                # insert selected milestone into table
                sel = req.args.get('sel')
                sel = isinstance(sel, list) and sel or [sel]
                db = self.env.get_db_cnx()
                for milestone in sel:
                    RT_Template.insert(self.env, milestone)
                db.commit()
                req.redirect(self.env.href.admin(cat, page))

        # get all enabled milestones
        enabledMilestones = RT_Template.getMilestones(self.env)

        ms = Milestone.select(self.env)
        ms.sort(cmp=lambda x,y: cmp(x.name, y.name))
        req.hdf['milestones'] = [{'name': m.name,
              'href': self.env.href.admin(cat, page, m.name),
              'enabled': m.name in enabledMilestones,
             } for m in ms]

        return 'admin_relaticket.cs', None

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
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'keylist'

    def get_navigation_items(self, req):
        """ hijack the original Trac's 'New Ticket' handler to ticket template
        """
        if not req.perm.has_permission('WIKI_VIEW'):
            return
        yield ('mainnav', 'keylist', 
               html.A(u'KeyList', href= req.href.keylist()))


    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/keylist')


    def process_request(self, req):
        req.perm.assert_permission('WIKI_VIEW')
        
        # setup permission
        really_has_perm = req.perm.has_permission('WIKI_VIEW')
        req.perm.perms['WIKI_VIEW'] = True
        if not really_has_perm:
            del req.perm.perms['WIKI_VIEW']

        filepath = '/'.join(req.path_info.split('/')[2:])
        if filepath:
            self._displayResultHtml(req, filepath)
        else:
            # display milestone list

            # get trac.ini
            projectName = self.env.config.get('project', 'name')

            db = self.env.get_db_cnx()
            curs = db.cursor()
            option = {}
            ul = []

            curs.execute("SELECT milestone FROM rt_template")
            reAllMilestone = [m[0] for m in curs.fetchall()]

            # strip milestone name
            milestone = []
            for m in reAllMilestone:
                mm = []
                for s in m.split("."):
                    try:
                        s.encode("ascii")
                        mm.append(s)
                    except:
                        break
                milestone.append(".".join(mm))

            data = []
            for m, m_full in zip(milestone, reAllMilestone):
                filename = "keylist/idx-%s.html" % m

                #ul.append('<li><a href="%s" title="%s">%s</a></li>' % (href, m_full, m_full))
                item = {
                        "filename":filename,
                        "m_full":m_full,
                        }

                data.append(item)

            req.hdf["data"] = data
            # return the cs template
            return 'keylist.cs', 0

    # private methods
    def _displayResultHtml(self, req, filepath):
        """  display result html
        """
        # get trac.ini
        base_path = self.env.config.get('rtadmin', 'base_path')


        # formart return string
        try:
            returnStr = open("%s/%s" % (base_path, filepath)).read()
        except:
            returnStr = "No result yet."

        self._sendResponse(req, returnStr)


    def _sendResponse(self, req, message):
        """ send response and stop request handling
        """
        req.send_response(200)
        req.send_header('Cache-control', 'must-revalidate')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', 'text/html' + ';charset=utf-8')
        req.send_header('Content-Length', len(message))
        req.end_headers()

        if req.method != 'HEAD':
            req.write(message)
        raise RequestDone
