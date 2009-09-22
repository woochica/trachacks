#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Aug 12, 2009

1. Connect to postgresql Database
2. Select ticket time
3. Generate ticket report

@author: Tod 
@email: junjie.jiang@hp.com
'''

import gethours
import time
import os
from pyExcelerator import *
from pkg_resources import resource_filename

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.admin import IAdminPanelProvider
from trac.web.chrome import *
from trac.env import IEnvironmentSetupParticipant
from trac.env import IEnvironmentSetupParticipant
from trac.util.translation import _
'''
because multiple projects alwasy got PROJECT_NAME_PREFIX like following format
 http://[ip]:[port]/PROJECT_NAME_PREFIX/[PROJECT_NAME]
if your environment is just single project like:
    http://[ip]:[port]/[PROJECT_NAME]
PROJECT_NAME_PREFIX="" # left it empty
'''
PROJECT_NAME_PREFIX= "/projects"
__all__ = ['AgiloTicketReport']

class TicketObj:
    def __init__(self, ticket_id,ticket_summary, ticket_owner, estimate_hours, 
        cost_hours, is_reopen):
        self.id = ticket_id
        self.summary = ticket_summary
        self.owner = ticket_owner
        self.esti_hours = estimate_hours
        self.cost_hours = cost_hours
        self.is_reopen = is_reopen

class TicketReportModule(Component):
    implements(ITemplateProvider,
               IAdminPanelProvider,
               IPermissionRequestor,
               )
    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['AGILO_TICKET_REPORT']
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
        return []

    # IAdminPanelProvider methods
    _type = 'AgiloTicketReport'
    _label = ('AgiloTicketReport', 'AgiloTicketReport')

    def get_admin_panels(self, req):
        if 'AGILO_TICKET_REPORT' in req.perm:
            yield ('agilo', 'Agilo', self._type, self._label[1])
    
    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('AGILO_TICKET_REPORT')
        data = {}
        data['sprint_list'] = self.get_sprint_list()
        data['milestone_list'] = self.get_milestone_list()
        
        if req.args.get('generate_data'):
            start_date = req.args.get("start_date")
            end_date = req.args.get("end_date")
            sprint = req.args.get("sprint")
            milestone = req.args.get("milestone")
            
            if start_date != "" and end_date != "":
               ##date format '2009/8/11 9:30:00' / '2009/08/30 18:00:00'
                start_date = time.strptime(start_date, '%Y/%m/%d %H:%M:%S')
                end_date = time.strptime(end_date,'%Y/%m/%d %H:%M:%S')
                t1 = time.mktime(start_date)
                t2 = time.mktime(end_date)	
                ticket_obj_list = self.query_by_date(t1.__str__(),t2.__str__())     
                data['report_title'] = self.format_date(t1)+ " - " +self.format_date(t2)  
            elif sprint != "":  
                ticket_obj_list = self.query_by_sprint(sprint)
                data['report_title'] = sprint
            else:
                ticket_obj_list = self.query_by_milestone(milestone)
                data['report_title'] = milestone
            data['ticket_obj_list'] = ticket_obj_list
            
        if req.args.get('generate_excel'):
            start_date = req.args.get("start_date")
            end_date = req.args.get("end_date")
            sprint = req.args.get("sprint")
            milestone = req.args.get("milestone")
            
            if start_date != "" and end_date != "":
              ##date format '2009/8/11 9:30:00' / '2009/08/30 18:00:00'
                start_date = time.strptime(start_date, '%Y/%m/%d %H:%M:%S')
                end_date = time.strptime(end_date,'%Y/%m/%d %H:%M:%S')
                t1 = time.mktime(start_date)
                t2 = time.mktime(end_date)
                ticket_obj_list = self.query_by_date(t1.__str__(),t2.__str__())  
                file_name = 'ticket_report_' + self.Format_date(t1) \
                +"-"+self.Format_date(t2) + '.xls'
            elif sprint != "":
                ticket_obj_list = self.query_by_sprint(sprint)
                file_name = sprint + ".xls"
            else:
                ticket_obj_list = self.query_by_milestone(milestone)
                file_name = milestone + ".xls"
                
            file_name = file_name.replace(" ","_")
            self.writeExcelReport(ticket_obj_list, file_name)
            # get project name path
            # handler both windows path and linux path, windows path split tag: "\\", linux : "/"
            project_name_path = PROJECT_NAME_PREFIX+"/"+ self.env.path.replace('\\','/').split('/')[-1]  #/           
            req.redirect(project_name_path + "/raw-attachment/report/ticket_report/" + file_name)
                
        return 'ticketreport.html', data
    
    
    def format_date(self, _date):
        return time.localtime(float(_date))[0].__str__()+"." \
    +time.localtime(float(_date))[1].__str__()+"."+time.localtime(float(_date))[2].__str__()

    def get_backlog_list(self, sql, db=None):
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(sql)
        closed_backlogs = list()
        running_backlogs = list()
        t = datetime.datetime.now()
        now = time.mktime(t.timetuple())
        
        for row in cursor.fetchall():
            _name, _start, _end = row
            if now > _end:
                #handler milestone
                if _end == 0:
                    running_backlogs.append(_name)
                closed_backlogs.append(_name)
            elif now >= _start and now <= _end:
                running_backlogs.append(_name)
            else:
                pass
            
        cursor.close()
                
        MAX_ITEMS = 10
        backlog_list = [
            {'label': _('Running (by Start Date)'),
             'options': running_backlogs},
            {'label': _('Closed (by End Date)'),
             'options': closed_backlogs[-MAX_ITEMS:]},
        ]
        return backlog_list
    
    def get_milestone_list(self):
        return self.get_backlog_list("select name,due,completed from milestone order by completed")
    def get_sprint_list(self):
        return self.get_backlog_list("select name,start,sprint_end from agilo_sprint order by sprint_end")
    
    def query_by_milestone(self, _milestone):
        getEstimateHourSQL = "select t1.ticket, t1.oldvalue from ticket_change t1 \
        left join ticket t on t.id =t1.ticket \
        where t1.field = 'remaining_time' and t1.time = (select min(t2.time) \
        from ticket_change t2 where t2.field = 'remaining_time' and t2.ticket=t1.ticket \
        and t2.oldvalue is not null) and t.milestone='%s'" % (_milestone)
        getStatusChangedSQL = "select tc.ticket,tc.newvalue,tc.time as time,t.owner, \
        t.time as ctime,t.summary from ticket_change tc left join ticket t \
        on tc.ticket=t.id where t.type='task' and tc.field = 'status' and \
        t.milestone='%s'" % (_milestone)
        return self.query_logic(getEstimateHourSQL, getStatusChangedSQL)
    
    def query_by_sprint(self, _sprint):
        getEstimateHourSQL = "select t1.ticket, t1.oldvalue from ticket_change t1 \
        where t1.field = 'remaining_time' and t1.time = (select min(t2.time) \
        from ticket_change t2 where t2.field = 'remaining_time' and t2.ticket=t1.ticket \
        and t2.oldvalue is not null) and t1.ticket in \
        (select tcm.ticket from ticket_custom tcm where tcm.value= '%s')" % (_sprint)
        getStatusChangedSQL = "select tc.ticket,tc.newvalue,tc.time as time,t.owner, \
        t.time as ctime,t.summary from ticket_change tc left join ticket t \
        on tc.ticket=t.id where t.type='task' and tc.field = 'status' and \
        tc.ticket in (select tcm.ticket from ticket_custom tcm where tcm.value='%s') \
         order by tc.ticket,tc.time desc" % (_sprint)
        return self.query_logic(getEstimateHourSQL, getStatusChangedSQL)
    
    def query_by_date(self, _start_date, _end_date, db=None):
        getEstimateHourSQL = "select t1.ticket, t1.oldvalue from ticket_change t1 \
        where t1.field = 'remaining_time' and t1.time = (select min(t2.time) \
        from ticket_change t2 where t2.field = 'remaining_time' and t2.ticket=t1.ticket \
         and t2.oldvalue is not null) and t1.time > %s and t1.time < %s" % (_start_date, _end_date)
        getStatusChangedSQL = "select tc.ticket,tc.newvalue,tc.time as time,t.owner, \
        t.time as ctime,t.summary from ticket_change tc left join ticket t \
        on tc.ticket=t.id where t.type='task' and tc.field = 'status' and \
        tc.time > %s and tc.time < %s order by tc.ticket,tc.time desc" % (_start_date, _end_date)
        return self.query_logic(getEstimateHourSQL, getStatusChangedSQL)

    def query_logic(self, _est_sql, _stc_sql, db=None):
        if not db:
            db = self.env.get_db_cnx()   
        cursor = db.cursor()
        
        cursor.execute(_est_sql)
        estimate_list = cursor.fetchall()
        cursor.execute(_stc_sql)
        status_change_list = cursor.fetchall()
        cursor.close()

        ticket = TicketObj(0,'','',0,0, False)
        instance = gethours.GetWorkingHours()
        temp_flag = True
        temp_closed_time = 0
        temp_ctime = 0
        list = []
        
        #handler last closed ticket
        status_change_list.append(["","",0,"",0,""])
        
        for row in status_change_list:
            s_ticket, s_newvalue, s_time, s_owner, s_ctime, s_summary = row
            if s_ticket == ticket.id:
                ticket.owner = s_owner
                ticket.summary = s_summary
                if s_newvalue == 'accepted':
                    ticket.cost_hours += instance.getTotalWorkingHours(s_time, temp_closed_time)
                    temp_flag = False
                elif temp_flag and (s_newvalue == 'reopened' or s_newvalue == 'assigned'):
                    ticket.cost_hours += instance.getTotalWorkingHours(s_time, temp_closed_time)
                else:
                    temp_closed_time = s_time
            else:
                if ticket.id != 0:
                    if temp_closed_time != 0 and ticket.cost_hours == 0:
                        ticket.cost_hours = instance.getTotalWorkingHours(temp_ctime, temp_closed_time)
                    if ticket.cost_hours != 0:
                        for erow in estimate_list:
                            e_ticket, e_oldvalue = erow
                            if e_ticket == ticket.id:
                                ticket.esti_hours = e_oldvalue
                        list.append(ticket)
                        ticket = TicketObj(0,'','',0,0,False)
                        
                    ticket.cost_hours = 0
                    temp_closed_time=0
                    temp_flag = True
                
                ticket.id = s_ticket
                if s_newvalue == 'closed':
                    temp_closed_time = s_time
                    temp_ctime = s_ctime
                    ticket.owner = s_owner
                    ticket.summary = s_summary
        
        list.sort(lambda x,y:cmp(x.owner,y.owner))
        
        return list
    
    def writeExcelReport(self,list,file_name,db=None):
        if not db:
            db = self.env.get_db_cnx() 
            handle_ta = True
        else:
            handle_ta = False
              
        cursor = db.cursor()
        cursor.execute("SELECT * FROM attachment WHERE filename ='"+file_name+"'")

        if not cursor.fetchone():
            cursor.execute("INSERT INTO attachment(\"type\", id, filename) \
            VALUES('report', 'ticket_report','"+file_name+"')")

            if handle_ta:
                db.commit()
    
        cursor.close()
                         
        w = Workbook()
        
        fnt = Font()
        fnt.name = 'Arial'
        fnt.colour_index = 4
        fnt.bold = True
        
        borders = Borders()
        borders.left = 6
        borders.right = 6
        borders.top = 6
        borders.bottom = 6
        
        al = Alignment()
        al.horz = Alignment.HORZ_CENTER
        al.vert = Alignment.VERT_CENTER
        
        style = XFStyle()
        style.font = fnt
        style.borders = borders
        style.alignment = al
        
        ws = w.add_sheet("ticket report")
        ws.write_merge(0,0,1,5, file_name.replace(".xls",""),style)
        ws.write(1,1, "ticket id")
        ws.write(1,2, "summary")
        ws.write(1,3, "owner")
        ws.write(1,4, "estimated time(hours)")
        ws.write(1,5, "cost time(hours)")
    
        for row in range(2, (list.__len__())+2):
            obj = list.pop(0)
            ws.write(row, 1, obj.id)
            ws.write(row, 2, obj.summary)
            ws.write(row, 3, obj.owner)
            ws.write(row, 4, int(obj.esti_hours.__str__()))
            ws.write(row, 5, obj.cost_hours)
            
        attachment_path = self.env.path.replace('\\','/') + "/attachments/report/ticket_report/" 
        if not os.access(attachment_path, os.F_OK):
            os.makedirs(attachment_path)       

        w.save(attachment_path + file_name)
        