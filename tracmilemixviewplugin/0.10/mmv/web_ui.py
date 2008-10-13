# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         web_ui.py
# Purpose:      The MMV Trac plugin handler module
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


from ChartDirector.pychartdir import *

from model import schema, schema_version, MMV_List

from utils import *

__all__ = ['MMVModule']

class MMVModule(Component):
    
    implements(ITemplateProvider, 
               IAdminPageProvider, 
               INavigationContributor, 
               IRequestHandler, 
               IEnvironmentSetupParticipant, 
               IPermissionRequestor,
               )

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['MMV_ADMIN']
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
                       "VALUES ('mmv_version',%s)", (schema_version,))

        db.commit()

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='mmv_version'")
        row = cursor.fetchone()
        if not row or int(row[0]) < schema_version:
            return True

    def upgrade_environment(self, db):
        
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='mmv_version'")
        row = cursor.fetchone()
        if not row:
            self.environment_created()
            current_version = 0
        else:    
            current_version = int(row[0])
            
        from mmv import upgrades
        for version in range(current_version + 1, schema_version + 1):
            for function in upgrades.map.get(version):
                print textwrap.fill(inspect.getdoc(function))
                function(self.env, db)
                print 'Done.'
        cursor.execute("UPDATE system SET value=%s WHERE "
                       "name='mmv_version'", (schema_version,))
        self.log.info('Upgraded MMV tables from version %d to %d',
                      current_version, schema_version)

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        self.env.log.info('get_admin_pages')

        if req.perm.has_permission('MMV_ADMIN'):
            yield 'ticket', 'Ticket', 'mmv_admin', 'MMV Admin'


    def process_admin_request(self, req, cat, page, milestone):
        req.perm.assert_permission('MMV_ADMIN')


        if req.args.get('save'):
            # save 

            # empty table first
            MMV_List.deleteAll(self.env)
            
            # insert selected milestone into table
            db = self.env.get_db_cnx()

            selReq = req.args.get('sel')
            milestoneReq = req.args.get('milestone')
            startdateReq = req.args.get('startdate')
            enddateReq = req.args.get('enddate')

            selList = isinstance(selReq, list) and selReq or [selReq]
            milestoneList = isinstance(milestoneReq, list) and milestoneReq or [milestoneReq]
            startdateList = isinstance(startdateReq, list) and startdateReq or [startdateReq]
            enddateList = isinstance(enddateReq, list) and enddateReq or [enddateReq]

            for milestone, startdate, enddate in zip(milestoneList, startdateList, enddateList):
                startdate = getDateFromStr(startdate)
                enddate = getDateFromStr(enddate)
                if milestone in selList:
                    enabled = True
                else:
                    enabled = False

                MMV_List.insert(self.env, milestone, startdate, enddate, enabled)
            db.commit()
            req.redirect(self.env.href.admin(cat, page))

        elif req.args.get('repair'):
            # repair 

            # empty table first
            MMV_List.deleteAllHistory(self.env)
            
            req.redirect(self.env.href.admin(cat, page))

        else:
            # display

            # get all enabled milestones
            enabledMilestones = MMV_List.getEnabledMilestones(self.env)

            ms = Milestone.select(self.env)
            ms.sort(cmp=lambda x,y: cmp(x.name, y.name))

            req.hdf['date_hint'] = "Format: YYYY/MM/DD"

            req.hdf['milestones'] = [{'name': m.name,
                  'href': self.env.href.admin(cat, "milestones", m.name),
                  'enabled': m.name in enabledMilestones,
                  'startdate':  formatDateFull(MMV_List.getStartdateFromDb(self.env, m.name)), 
                  'enddate': formatDateFull(MMV_List.getEnddateFromDb(self.env, m.name)),
                 } for m in ms]

            return 'mmv_admin.cs', None

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
        return [('mmv', resource_filename(__name__, 'htdocs'))]
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'mmv'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('WIKI_VIEW'):
            return
        mmv_title = self.config.get("mmv", "mmv_title", "MMV")
        yield ('mainnav', 'mmv', 
               html.A(mmv_title, href= req.href.mmv()))


    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/mmv')


    def process_request(self, req):
        req.perm.assert_permission('WIKI_VIEW')
        
        # setup permission
        really_has_perm = req.perm.has_permission('WIKI_VIEW')
        req.perm.perms['WIKI_VIEW'] = True
        if not really_has_perm:
            del req.perm.perms['WIKI_VIEW']

        if req.path_info.startswith('/mmv/mmv_view'):
            # display milestone mmv view
            today = int(time.time()) / SECPERDAY

            pathSegments = req.path_info.split('/')
            milestone = pathSegments[3]

            if req.method == "POST":
                go_date = req.args.get("go_date")
                go_date = getDateFromStr(go_date)
                if not go_date:
                    cur_date = today
                else:
                    cur_date = go_date / SECPERDAY + 1
            else:
                cur_date = req.args.get("date")
                if not cur_date:
                    cur_date = int(time.time()) / SECPERDAY
                cur_date = int(cur_date)

            if cur_date > today:
                cur_date = today

            prev_date = cur_date - 1

            next_date = cur_date + 1
            if next_date > today:
                next_date = today

            req.hdf['milestone'] = milestone
            req.hdf['burndown_png'] = req.href.chrome('mmv', 'burndown.png')
            req.hdf['members_png'] = req.href.chrome('mmv', 'members.png')

            # puredata, reladata
            puredata, reladata, unplanneddata = self._relaTicketView(req, milestone, cur_date)
            req.hdf['puredata'] = puredata
            req.hdf['reladata'] = reladata
            req.hdf['unplanneddata'] = unplanneddata

            # member_list
            memberList = self._getMemberList(milestone)
            req.hdf['member_list'] = memberList

            req.hdf['cur_date'] = cur_date
            req.hdf['prev_date'] = prev_date
            req.hdf['next_date'] = next_date

            req.hdf['cur_date_str'] = formatDateFull(cur_date * SECPERDAY)
            
            req.hdf['enable_unplanned'] = self.config.getbool("mmv", "enable_unplanned", True)
            req.hdf['enable_relaticket'] = self.config.getbool("mmv", "enable_relaticket", True)
    
            return 'mmv_view.cs', None

        elif req.path_info.startswith('/mmv/burndown'):
            # display mmv burndown image
            pathSegments = req.path_info.split('/')
            returnStr = ""
            if len(pathSegments) == 5:
                milestone = pathSegments[3]
                date = int(pathSegments[4][:-4])

                # get img string
                returnStr = self._getBurndownImgStr(milestone, date)

            _sendResponse(req, returnStr)

        elif req.path_info.startswith('/mmv/date'):
            
            pathSegments = req.path_info.split('/')
            returnStr = ""
            if len(pathSegments) == 5:
                # display worktime image one day
                milestone = pathSegments[3]
                date = int(pathSegments[4][:-4])

                # get img string
                returnStr = self._getDateImgStr(milestone, date)

            _sendResponse(req, returnStr)

        elif req.path_info.startswith('/mmv/members'):
            pathSegments = req.path_info.split('/')

            if len(pathSegments) == 4:
                # display all members worktime image
                imgname = pathSegments[3]
                milestone = imgname[:-4]

                # get img string
                returnStr = self._getAllMembersImgStr(milestone)

                _sendResponse(req, returnStr)

            elif len(pathSegments) == 5:
                # display one member worktime image
                member = pathSegments[3]
                imgname = pathSegments[4]
                milestone = imgname[:-4]

                # get img string
                returnStr = self._getMemberImgStr(milestone, member)

                _sendResponse(req, returnStr)

        elif req.path_info == "/mmv":
            # display milestone list
            enabledMilestones = MMV_List.getEnabledMilestones(self.env)

            # strip milestone name
            milestone = []
            for m in enabledMilestones:
                milestone.append(m)

            today = int(time.time()) / SECPERDAY

            data = []
            for m, m_full in zip(milestone, enabledMilestones):
                filename = "mmv/mmv_view/%s" % (m, )

                item = {
                        "filename":filename,
                        "m_full":m_full,
                        }

                data.append(item)

            req.hdf["data"] = data
            # return the cs template
            return 'mmv_list.cs', 0

    # private methods
    def _getDateList(self, milestone):
        """ get all dates of a milestone
        """
        # get min milestone date
        startdate = MMV_List.getStartdate(self.env, milestone)
        # get max milestone date
        enddate = MMV_List.getEnddate(self.env, milestone)

        

        dateMin = int(startdate) / SECPERDAY
        dateMax = int(enddate) / SECPERDAY

        dateList = range(dateMax, dateMin - 1, -1)

        return dateList

    def _getMemberList(self, milestone):
        """ get all members
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        cursor.execute("SELECT DISTINCT owner FROM ticket "
                       "WHERE milestone = '%s' ORDER BY owner;" % milestone)
        rows = cursor.fetchall()

        memberList = [row[0] for row in rows]

        return memberList

    def _getAllMembersImgStr(self, milestone):
        """ get all members image string
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # prepare chart data
        # init chart data
        chartData = {}

        # genearte chart
        subMilestone = stripMilestoneName(milestone)
        returnStr = self._genLineChart(chartData, subMilestone, subMilestone)

        return returnStr

    def _getDateImgStr(self, milestone, date):
        """ get one day image string
        """
        memberList = self._getMemberList(milestone)

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # prepare chart data
        # init chart data
        chartData = {"due":{},
                     "done":{},
                    }


        # get history data from db
        # get min milestone date
        startdate = MMV_List.getStartdate(self.env, milestone)
        # get max milestone date
        enddate = MMV_List.getEnddate(self.env, milestone)

        dateMin = int(startdate) / SECPERDAY
        dateMax = int(enddate) / SECPERDAY

        # due
        for member in memberList:
            dateEndTime = (date + 1) * SECPERDAY

            sqlString = """
                SELECT tc.ticket, tc.name, tc.value 
                FROM ticket_custom tc, ticket t 
                WHERE tc.ticket = t.id 
                AND tc.name = '%(duetime)s' 
                AND t.id IN (
                    SELECT ta.id FROM 
                    (SELECT id
                     FROM ticket
                     WHERE time < %(dateEndTime)s  AND owner = '%(member)s' ) AS ta 
                     LEFT JOIN
                    (SELECT DISTINCT B.ticket AS ticket, B.time AS time, A.newvalue AS newvalue
                     FROM ticket_change A,
                     (SELECT  ticket, max(time) AS time
                     FROM ticket_change 
                     WHERE field = 'status' 
                     AND time < %(dateEndTime)s
                     GROUP BY ticket 
                     ORDER BY ticket) AS B
                     WHERE A.ticket = B.ticket 
                     AND A.time = B.time
                     AND A.field = 'status'
                     AND newvalue IN ('closed','reopened') ) AS tb 
                     ON ta.id = tb.ticket
                     WHERE tb.newvalue != 'closed' OR tb.newvalue IS NULL
                     )  
                AND t.milestone = '%(milestone)s';
            """ % {'dateEndTime':dateEndTime, 
                    'milestone':milestone, 
                    'member':member, 
                    'duetime':_getDueField(self.config), }

            cursor.execute(sqlString)
            rows = cursor.fetchall()

            # calculate total due days
            dueDays = 0
            for row in rows:
                duetime = row[2]
                dueDays += dueday(duetime)

            chartData["due"][member] = dueDays


        # done
        for member in memberList:
            dateEndTime = (date + 1) * SECPERDAY

            sqlString = """
                SELECT tc.ticket, tc.name, tc.value 
                FROM ticket_custom tc, ticket t 
                WHERE tc.ticket = t.id 
                AND tc.name = '%(duetime)s' 
                AND t.id IN (
                    SELECT ta.id FROM 
                    (SELECT id
                     FROM ticket
                     WHERE time < %(dateEndTime)s  AND owner = '%(member)s' ) AS ta 
                     LEFT JOIN
                    (SELECT DISTINCT B.ticket AS ticket, B.time AS time, A.newvalue AS newvalue
                     FROM ticket_change A,
                     (SELECT  ticket, max(time) AS time
                     FROM ticket_change 
                     WHERE field = 'status' 
                     AND time < %(dateEndTime)s
                     GROUP BY ticket 
                     ORDER BY ticket) AS B
                     WHERE A.ticket = B.ticket 
                     AND A.time = B.time
                     AND A.field = 'status'
                     AND newvalue IN ('closed','reopened') ) AS tb 
                     ON ta.id = tb.ticket
                     WHERE tb.newvalue = 'closed'
                     )  
                AND t.milestone = '%(milestone)s';
            """ % {'dateEndTime':dateEndTime, 
                    'milestone':milestone, 
                    'member':member, 
                    'duetime':_getDueField(self.config), }

            cursor.execute(sqlString)
            rows = cursor.fetchall()

            # calculate total due days
            dueDays = 0
            for row in rows:
                duetime = row[2]
                dueDays += dueday(duetime)

            chartData["done"][member] = dueDays

        # genearte chart
        subMilestone = stripMilestoneName(milestone)
        title = subMilestone + ": " + formatDateFull(date * SECPERDAY)
        returnStr = self._genBarChart(chartData, subMilestone, title)

        return returnStr


    def _getMemberImgStr(self, milestone, member):
        """ get one member image string
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # prepare chart data
        # init chart data
        chartData = {"due":{},
                     "done":{},
                    }


        # get history data from db
        # get min milestone date
        startdate = MMV_List.getStartdate(self.env, milestone)
        # get max milestone date
        enddate = MMV_List.getEnddate(self.env, milestone)

        dateMin = int(startdate) / SECPERDAY
        dateMax = int(enddate) / SECPERDAY

        # due
        for aDay in range(dateMin, dateMax + 1):
            dateString = formatDateCompact(aDay * SECPERDAY)
            dateEndTime = (aDay + 1) * SECPERDAY

            sqlString = """
                SELECT tc.ticket, tc.name, tc.value 
                FROM ticket_custom tc, ticket t 
                WHERE tc.ticket = t.id 
                AND tc.name = '%(duetime)s' 
                AND t.id IN (
                    SELECT ta.id FROM 
                    (SELECT id
                     FROM ticket
                     WHERE time < %(dateEndTime)s  AND owner = '%(member)s' ) AS ta 
                     LEFT JOIN
                    (SELECT DISTINCT B.ticket AS ticket, B.time AS time, A.newvalue AS newvalue
                     FROM ticket_change A,
                     (SELECT  ticket, max(time) AS time
                     FROM ticket_change 
                     WHERE field = 'status' 
                     AND time < %(dateEndTime)s
                     GROUP BY ticket 
                     ORDER BY ticket) AS B
                     WHERE A.ticket = B.ticket 
                     AND A.time = B.time
                     AND A.field = 'status'
                     AND newvalue IN ('closed','reopened') ) AS tb 
                     ON ta.id = tb.ticket
                     WHERE tb.newvalue != 'closed' OR tb.newvalue IS NULL
                     )  
                AND t.milestone = '%(milestone)s';
            """ % {'dateEndTime':dateEndTime, 
                    'milestone':milestone, 
                    'member':member, 
                    'duetime':_getDueField(self.config), }

            cursor.execute(sqlString)
            rows = cursor.fetchall()

            # calculate total due days
            dueDays = 0
            for row in rows:
                duetime = row[2]
                dueDays += dueday(duetime)

            chartData["due"][dateString] = dueDays


        # done
        for aDay in range(dateMin, dateMax + 1):
            dateString = formatDateCompact(aDay * SECPERDAY)
            dateEndTime = (aDay + 1) * SECPERDAY

            sqlString = """
                SELECT tc.ticket, tc.name, tc.value 
                FROM ticket_custom tc, ticket t 
                WHERE tc.ticket = t.id 
                AND tc.name = '%(duetime)s' 
                AND t.id IN (
                    SELECT ta.id FROM 
                    (SELECT id
                     FROM ticket
                     WHERE time < %(dateEndTime)s  AND owner = '%(member)s' ) AS ta 
                     LEFT JOIN
                    (SELECT DISTINCT B.ticket AS ticket, B.time AS time, A.newvalue AS newvalue
                     FROM ticket_change A,
                     (SELECT  ticket, max(time) AS time
                     FROM ticket_change 
                     WHERE field = 'status' 
                     AND time < %(dateEndTime)s
                     GROUP BY ticket 
                     ORDER BY ticket) AS B
                     WHERE A.ticket = B.ticket 
                     AND A.time = B.time
                     AND A.field = 'status'
                     AND newvalue IN ('closed','reopened') ) AS tb 
                     ON ta.id = tb.ticket
                     WHERE tb.newvalue = 'closed'
                     )  
                AND t.milestone = '%(milestone)s';
            """ % {'dateEndTime':dateEndTime, 
                    'milestone':milestone, 
                    'member':member, 
                    'duetime':_getDueField(self.config), }

            cursor.execute(sqlString)
            rows = cursor.fetchall()

            # calculate total due days
            dueDays = 0
            for row in rows:
                duetime = row[2]
                dueDays += dueday(duetime)

            chartData["done"][dateString] = dueDays


        print chartData

        # genearte chart
        subMilestone = stripMilestoneName(milestone)
        returnStr = self._genLineChart(chartData, subMilestone, member)

        return returnStr

    def _getBurndownImgStr(self, milestone, date):
        """ get burndown image string
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # prepare chart data
        # init chart data
        chartData = {"due":{},
                     "done":{},
                    }

        # get history data from db
        # get min milestone date
        startdate = MMV_List.getStartdate(self.env, milestone)
        # get max milestone date
        enddate = MMV_List.getEnddate(self.env, milestone)
        if not startdate:
            # no ticket in this milestone
            # skip
            return ""

        dateMin = int(startdate) / SECPERDAY + 1
        dateMax = int(enddate) / SECPERDAY + 1
        if dateMax > date:
            dateMax = date


        max_history_date = MMV_List.getMaxHistoryDate(self.env, milestone)
        # add history
        for add_date in range(dateMin, dateMax + 1):
            if add_date < max_history_date - 2:
                # don't update stable history
                continue
            MMV_List(self.env).addHistory(self.env, add_date, milestone)

        # get due
        dueData = MMV_List.getDue(self.env, dateMin, dateMax, milestone)
        for date, dueDays in dueData:
            dateString = formatDateCompact(date * SECPERDAY)
            chartData["due"][dateString] = dueDays

        # get done
        doneData = MMV_List.getDue(self.env, dateMin, dateMax, milestone)
        for date, doneDays in doneData:
            dateString = formatDateCompact(date * SECPERDAY)
            chartData["done"][dateString] = doneDays

        # genearte chart
        subMilestone = stripMilestoneName(milestone)
        returnStr = self._genLineChart(chartData, subMilestone, subMilestone)

        return returnStr

    def _genBarChart(self, chartData, subMilestone, title):
        ''' generate pie chart
        '''
        print chartData
        # The data for the bar chart
        labels = [str(label) for label in chartData["due"].keys()]
        labels.sort()
        #labels.reverse()
        dataDue = [float(chartData["due"][label]) for label in labels]
        dataDone = [float(chartData["done"][label]) for label in labels]

        # The labels for the bar chart

        defaultfont = "normal"

        # The data for the line chart

        pwidth = len(labels) * 80
        cwidth = 100 + pwidth

        pheight = 15 * max(dataDue)
        if pheight < 100:
            pheight = 100
        if pheight > 1000:
            pheight = 1000
        cheight = 120 + pheight
        
        c = XYChart(cwidth,cheight, 0xffffc0, 0x000000, 1)
        
        c.addLegend(40, 15, 0, "", 8).setBackground(Transparent)
        c.setPlotArea(40, 50, pwidth,pheight
            , c.linearGradientColor(0, 35, 0, 235, 0xf9fcff,0xaaccff)
            , -1, Transparent, 0xffffff)
        
        c.setBackground(goldColor(), 0x334433, 1) #metalColor(0xccccff)
        c.setRoundedFrame()
        c.setDefaultFonts(defaultfont)
        
        c.addTitle(str(title), defaultfont, 11,0xffffff
            ).setBackground(c.patternColor([0x004000, 0x008000], 2))

        c.yAxis().setLabelFormat("{value}")
        c.xAxis().setLabels(labels).setFontAngle(30)#.setFontAngle(90)
        c.yAxis().setWidth(2)
        c.xAxis().setWidth(2)

        layer = c.addBarLayer2(Stack)
        layer.setBarShape(CircleShape)
        layer.addDataSet(dataDue, 0xcf4040, "Due(day)")
        layer.addDataSet(dataDone, 0x40cf40, "Done(day)")
#        layer.setLineWidth(4)
#        layer.addDataSet(dataDue, 0xcf4040, "Due(day)").setDataSymbol(CircleSymbol, 9,0xffff00)
#        layer.addDataSet(dataDone, 0x40cf40, "Done(day)").setDataSymbol(CircleSymbol, 9,0xffff00)
#        layer.setDataLabelFormat("{value|1}")
#        layer.setDataLabelStyle(defaultfont, 8, 0x334433, 0)
        layer.setBarGap(0.2, TouchBar)
        layer.setAggregateLabelStyle("arialbd.ttf", 8, layer.yZoneColor(0, 0xcc3300, 0x3333ff))
        layer.setDataLabelStyle()

        return c.makeChart2(PNG)


    def _genLineChart(self, chartData, subMilestone, title):
        ''' generate chart
        '''
        # The data for the bar chart
        labels = [str(label) for label in chartData["due"].keys()]
        labels.sort()
        labels.reverse()
        dataDue = [float(chartData["due"][label]) for label in labels]
        dataDone = [float(chartData["done"][label]) for label in labels]

        # The labels for the bar chart

        defaultfont = "normal"

        # The data for the line chart

        pwidth = len(labels)*18
        cwidth = 80 + pwidth

        pheight = 2 * max(dataDue)
        if pheight < 60:
            pheight = 60
        if pheight > 1000:
            pheight = 1000
        cheight = 100 + pheight
        
        c = XYChart(cwidth,cheight, 0xffffc0, 0x000000, 1)
        
        c.addLegend(40, 15, 0, "", 8).setBackground(Transparent)
        c.setPlotArea(40, 50, pwidth,pheight
            , c.linearGradientColor(0, 35, 0, 235, 0xf9fcff,0xaaccff)
            , -1, Transparent, 0xffffff)
        
        c.setBackground(goldColor(), 0x334433, 1) #metalColor(0xccccff)
        c.setRoundedFrame()
        c.setDefaultFonts(defaultfont)
        
        c.addTitle(str(title), defaultfont, 11,0xffffff
            ).setBackground(c.patternColor([0x004000, 0x008000], 2))

        c.yAxis().setLabelFormat("{value}")
        c.xAxis().setLabels(labels).setFontAngle(30)#.setFontAngle(90)
        c.yAxis().setWidth(2)
        c.xAxis().setWidth(2)
        
        layer = c.addSplineLayer() #addLineLayer()
        layer.setLineWidth(4)
        layer.addDataSet(dataDue, 0xcf4040, "Due(day)").setDataSymbol(CircleSymbol, 9,0xffff00)
        if self.config.getbool("mmv", "show_burndown_done", False):
            layer.addDataSet(dataDone, 0x40cf40, "Done(day)").setDataSymbol(CircleSymbol, 9,0xffff00)
#        layer.setDataLabelFormat("{value|1}")
        layer.setDataLabelStyle(defaultfont, 8, 0x334433, -90)

        return c.makeChart2(PNG)

    def _relaTicketView(self, req, milestone, date):
        """ display rela ticket view
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # gen ticket id -> summary mapping
        ticketMapping = {}
        cursor.execute('SELECT id, status, summary FROM ticket;')
        rows = cursor.fetchall()
        for id, status, summary in rows:
            ticketMapping[id] = summary

        # get relaAll
#        sqlString = '''SELECT ticket, max(time), newvalue 
#                 FROM ticket_change 
#                 WHERE field = 'status' 
#                 AND time < %s 
#                 GROUP BY ticket;'''  % ((date + 1) * SECPERDAY)

        sqlString = """SELECT DISTINCT B.ticket AS ticket, B.time AS time, A.newvalue AS newvalue
                     FROM ticket_change A,
                     (SELECT  ticket, max(time) AS time
                     FROM ticket_change 
                     WHERE field = 'status' 
                     AND time < %s 
                     GROUP BY ticket 
                     ORDER BY ticket) AS B
                     WHERE A.ticket = B.ticket 
                     AND A.time = B.time
                     AND A.field = 'status';"""  % ((date + 1) * SECPERDAY)

        cursor.execute(sqlString)
        rowsChange = cursor.fetchall()

        ticketStatusMapping = {}
        for row in rowsChange:
            ticketStatusMapping[row[0]] = row[2]

        sqlString = """SELECT id, status, summary 
                        FROM ticket 
                        WHERE milestone = '%s' 
                        AND time < %s;"""  % (milestone, (date + 1) * SECPERDAY)
        cursor.execute(sqlString)
        rows = cursor.fetchall()

        # convert to list
        rowsNew = []
        for row in rows:
            rowsNew.append(list(row))

        # update ticket status at the time
        for row in rowsNew:
            id = row[0]
            if id in ticketStatusMapping:
                row[1] = ticketStatusMapping[id]
            else:
                row[1] = "new"


        relaAll = self._getRelaAll(rowsNew)

        # prepare data for template
        
        # pure entries
        puredata = {
            'purenew':[],
            'puredoing':[],
            'puredone':[],
        }

        for tag in ('purenew', 'puredoing', 'puredone' ):
            for id in relaAll[tag]:
                summary = ticketMapping[id]
                puredata[tag].append({'id':id, 'summary':summary,})


        # rela tickets
        reladata = []

        for parentId, relati in relaAll['relati'].items():
            relarow = {
                'parent': {},
                'new':[],
                'doing':[],
                'done':[],
                }

            # parent ticket
            summary = ticketMapping[int(parentId)]
            relarow['parent'] = {'id':parentId, 'summary':summary,}

            # sub tickets
            for tag in ('new', 'doing', 'done' ):
                for id in relati[tag]:
                    summary = ticketMapping[id]
                    relarow[tag].append({'id':id, 'summary':summary,})

            reladata.append(relarow)

        # unplanned
        UNPLANNED = self.config.get("mmv", "unplanned")
        cursor.execute("SELECT id, status, summary FROM ticket "
                       "WHERE milestone = '%s' AND time < %s AND summary LIKE '%s%%';" 
                    % (milestone, (date + 1) * SECPERDAY, UNPLANNED) )
        rows = cursor.fetchall()
        unplanned = [row[0] for row in rows]

        unplanneddata = []
        for id in unplanned:
            summary = ticketMapping[id]
            unplanneddata.append({'id':id, 'summary':summary,})

        return puredata, reladata, unplanneddata


    def _getRelaAll(self, rows):
        """ get relaAll structure
        """
        relaAll = {
            'purenew': [],
            'puredoing': [], 
            'puredone': [], 
            'relati': {}, 
            }
        
        for id, status, summary in rows:
            # handle summary
            if '<#'== summary[:2]:
                # sub ticket
                parentID = int(summary.split(">")[0][2:])

                if parentID not in relaAll['relati'].keys():
                    # init parent entry
                    relaAll['relati'][parentID] = {'new':[],
                                                    'doing':[],
                                                    'done':[]}
                
                # remove main ticket from pure tickets
                if parentID in relaAll['purenew']:
                    relaAll['purenew'].remove(parentID)
                elif parentID in relaAll['puredoing']:
                    relaAll['puredoing'].remove(parentID)
                elif parentID in relaAll['puredone']:
                    relaAll['puredone'].remove(parentID)


                # add sub ticket to parent entry
                if status in ('new', 'reopened'):
                    relaAll['relati'][parentID]['new'].append(id)
                elif status == 'assigned':
                    relaAll['relati'][parentID]['doing'].append(id)
                elif status == 'closed':
                    relaAll['relati'][parentID]['done'].append(id)
            else:
                # not sub tickets
                if id not in relaAll['relati'].keys():
                    # assume they are pure tickets
                    # add to pure entries
                    if status == 'new':
                        relaAll['purenew'].append(id)
                    elif status == 'assigned':
                        relaAll['puredoing'].append(id)
                    elif status == 'closed':
                        relaAll['puredone'].append(id)

                else:
                    # main ticket
                    # ignore
                    pass

        return relaAll


def _sendResponse(req, message):
    """ send response and stop request handling
    """
    req.send_response(200)
    req.send_header('Cache-control', 'must-revalidate')
    req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
    req.send_header('Content-Type', 'image/png')
    req.send_header('Content-Length', len(message))
    req.end_headers()

    if req.method != 'HEAD':
        req.write(message)
    raise RequestDone

def _getDueField(config):
    return config.get("mmv", "ticket_custom_due", "duetime")



