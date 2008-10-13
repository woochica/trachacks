# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         reportmanager.py
# Purpose:      The report manager Trac plugin handler module
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

from trac.admin import IAdminPanelProvider

from pkg_resources import resource_filename

import os
import pickle
import inspect
import time
import textwrap

import xml.dom.minidom as minidom

from model import schema, schema_version, ReportHistory

__all__ = ['ReportManagerModule']

class ReportManagerModule(Component):
    ticket_manipulators = ExtensionPoint(ITicketManipulator)
    
    implements(ITemplateProvider, 
               IAdminPanelProvider, 
               IEnvironmentSetupParticipant, 
               IPermissionRequestor,
               )

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['REPORT_ADMIN']
        return actions


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
        return [('report_manager', resource_filename(__name__, 'htdocs'))]

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
                       "VALUES ('report_manager_version',%s)", (schema_version,))

        db.commit()

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='report_manager_version'")
        row = cursor.fetchone()
        if not row or int(row[0]) < schema_version:
            return True

    def upgrade_environment(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='report_manager_version'")
        row = cursor.fetchone()
        if not row:
            self.environment_created()
            current_version = 0
        else:    
            current_version = int(row[0])
            
        import upgrades
        for version in range(current_version + 1, schema_version + 1):
            for function in upgrades.map.get(version):
                print textwrap.fill(inspect.getdoc(function))
                function(self.env, db)
                print 'Done.'
        cursor.execute("UPDATE system SET value=%s WHERE "
                       "name='report_manager_version'", (schema_version,))
        self.log.info('Upgraded report manager tables from version %d to %d',
                      current_version, schema_version)
    

    # IAdminPanelProvider methods
    _type = 'reportmanager'
    _label = ('Report Manager', 'Report Manager')

    def get_admin_panels(self, req):
        if 'REPORT_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', self._type, self._label[1])

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('REPORT_ADMIN')

        data = {}

        loadHistoryId = ""
        delHistoryId = ""
        editHistoryId = ""
        for key in req.args.keys():
            if key.startswith("load_"):
                loadHistoryId = key[len("load_"):]
                break

        for key in req.args.keys():
            if key.startswith("del_"):
                delHistoryId = key[len("del_"):]
                break

        for key in req.args.keys():
            if key.startswith("edit_"):
                editHistoryId = key[len("edit_"):]
                break

        # load
        if loadHistoryId:
            self._loadHistory(req, loadHistoryId)
            # redirect to report page
            req.redirect(req.href.report())

        # del
        elif delHistoryId:
            self._delHistory(req, delHistoryId)

        # edit
        elif editHistoryId:

            data['editHistoryId'] = editHistoryId
            data['reports_log'] = ReportHistory.getLogById(self.env, editHistoryId)

            reports = self._getHistoryReports(req, editHistoryId)
            report_list = []
            for id, title, description, query in reports:
                report_entry = {}
                report_entry["id"] = id
                report_entry["title"] = title
                report_entry["description"] = description
                report_entry["query"] = query
                report_entry["href"] = req.abs_href.admin(cat, page, {"report_id":id})
                report_list.append(report_entry)
            
            data['report_list'] = report_list

            return 'editreports.html', data

        # Save
        elif req.args.get('savereport'):
            self._saveHistory(req)

        # apply edit history
        elif req.args.get('applyedit'):
            self._applyHistoryModify(req)

        # apply edit history
        elif req.args.get('cancel'):
            pass


        # prepare template page
        report_history = []
        for id, save_time, reports_log, reports_content in ReportHistory.getReportsHistory(self.env):
            history = {}
            history["id"] = id
            history["save_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(save_time)))
            history["reports_log"] = reports_log
            report_history.append(history)
        
        report_history.reverse()
        data['report_history'] = report_history

        return 'admin_report.html', data

    # private methods
    def _applyHistoryModify(self, req):
        """ edit reports history """

        # get new_id : orig_id mapping
        reportMapping = {}
        for key in req.args.keys():
            if key.startswith("report_"):
                origId = int(key[len("report_"):])
                try:
                    newId = int(req.args.get(key))
                except ValueError:
                    raise TracError, "Report id must be integer."
                # check errors
                if newId < 1:
                    raise TracError, "Report id must be great than zero."
                if newId in reportMapping:
                    raise TracError, "Report id must be unique."
                
                reportMapping[newId] = origId
        

        # get all orig reports
        origReportsMapping = {}
        historyId = req.args["history_id"]
        origReports = self._getHistoryReports(req, historyId)
        for id, title, description, query in origReports:
            origReportsMapping[id] = (title, description, query)

        # gen new reports
        newReports = []
        newIds = reportMapping.keys()
        newIds.sort()
        for newId in newIds:
            origId = reportMapping[newId]
            # 
            title, description, query = origReportsMapping[origId]
            newReports.append((newId, title, description, query))

        # gen report doc elem
        reportDoc = self._genReportDoc(newReports)
        # save reports status
        reports_log = req.args.get("reports_log")
        if not reports_log:
            reports_log = "based on #%s" % historyId

        self._saveReportFile(reports_log, reportDoc)


    def _getHistoryReports(self, req, historyId):
        """ get history reports """
        reports_content = ReportHistory.fetchById(self.env, historyId)

        # parse reports xml
        reports = self._parseReports(reports_content)

        return reports


    def _delHistory(self, req, delHistoryId):
        """ del reports history """
        ReportHistory.delete(self.env, delHistoryId)

    def _loadHistory(self, req, loadHistoryId):
        """ load reports history """
        reports_content = ReportHistory.fetchById(self.env, loadHistoryId)

        # parse reports xml
        reports = self._parseReports(reports_content)

        # clean up reports
        self._cleanUpReports()

        # insert reports
        for report in reports:
            self._insertReport(report)

    def _saveHistory(self, req):
        """ save report history """
        ## get settings from trac.ini
        #svn = self.config.get("reportmanager","svn")
        # get all reports
        reports = self._fetchReports()
        # gen report doc elem
        reportDoc = self._genReportDoc(reports)
        # save reports status
        reports_log = req.args.get("reports_log")
        if not reports_log:
            reports_log = "reports history at %s" % self._now()

        self._saveReportFile(reports_log, reportDoc)


    def _parseReports(self, reports_content):
        """ parse reports xml content 
            return reports list
        """
        reports = []

        # parse xml string, get reportsElem
        try:
            reportsDom = minidom.parseString(reports_content.encode("utf-8"))
            reportsElems = reportsDom.getElementsByTagName("reports")
            reportsElem = reportsElems[0]
        except:
            return reports
        
        # gen reports
        for reportElem in reportsElem.childNodes:
            id = int(self._getNodeText(reportElem, "id"))
            title = self._getNodeText(reportElem, "title")
            description = self._getNodeText(reportElem, "description")
            query = self._getNodeText(reportElem, "query")
            reports.append((id, title, description, query))
        
        return reports

    def _getNodeText(self, nodeElem, tag):
        """ get node text """
        try:
            return nodeElem.getElementsByTagName(tag)[0].firstChild.data
        except:
            return ""

    def _genReportDoc(self, reports):
        reportImpl = minidom.getDOMImplementation()
        reportDoc = reportImpl.createDocument(None, "tracreports", None)
        topElement = reportDoc.documentElement

        self._appendNode(reportDoc, topElement, 'project', self.config.get("project","name"))
        #self._appendNode(reportDoc, topElement, 'save_time', self._now())

        reportsNode = reportDoc.createElement('reports')
        topElement.appendChild(reportsNode)


        for id, title, description, query in reports:
            reportNode = reportDoc.createElement('report')
            reportsNode.appendChild(reportNode)
            
            # set values
            self._appendNode(reportDoc, reportNode, 'id', str(id))
            self._appendNode(reportDoc, reportNode, 'title', title)
            self._appendNode(reportDoc, reportNode, 'description', description)
            self._appendNode(reportDoc, reportNode, 'query', query)

        return reportDoc

    def _appendNode(self, doc, parentNode, nodeName, nodeText):
        childNode = doc.createElement(nodeName)
        parentNode.appendChild(childNode)
        textNode = doc.createTextNode(nodeText)
        childNode.appendChild(textNode)


    def _saveReportFile(self, reports_log, reportDoc):
        """
            Save report xml file
        """
        # gen reports_content
        reports_content = reportDoc.toxml().encode("utf-8")
        # insert into db
        ReportHistory.insert(self.env, reports_log, reports_content, int(time.time()))

        ## write to file
        #reportFile = open("/reports.xml", "w")
        #reportFile.write(reports_content)
        #reportFile.close()

    def _insertReport(self, report, db=None):
        """insert report table."""

        id,title,description,query = report

        if not db:
            db = self.env.get_db_cnx()

        cursor = db.cursor()
        
        cursor.execute("INSERT INTO report "
                       "(id,title,description,query) VALUES (%s,%s,%s,%s)",
                       (id,title,description,query))
        db.commit()

    def _cleanUpReports(self, db=None):
        """clean up report table."""
        if not db:
            db = self.env.get_db_cnx()

        cursor = db.cursor()
        
        cursor.execute("DELETE FROM report")
        db.commit()

    def _fetchReports(self, db=None):
        """Retrieve all reports."""
        if not db:
            db = self.env.get_db_cnx()

        cursor = db.cursor()
        
        cursor.execute("SELECT id, title, description, query  FROM report ORDER BY id")
        
        reports = cursor.fetchall()
        return reports


    def _now(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
