from datetime import datetime, timedelta
import time

from trac.util.html import Markup
from trac.wiki.macros import WikiMacroBase
from trac.wiki.api import parse_args
import copy

DEFAULT_OPTIONS = {'owner': '$USER'}

class TimeTable(WikiMacroBase):
    
    def render_macro(self, req, name, content):
        
        _, parsed_options = parse_args(content, strict=False)
        options = copy.copy(DEFAULT_OPTIONS)
        options.update(parsed_options)
        
        view = self.render(req, options)
        
        return Markup(view)

    def render(self, req, options):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        where = "t.STATUS<>'closed' AND t.STATUS<>'resolved' AND t.OWNER='%s'" % (options['owner']);
        orderBy = "start.VALUE ASC";
        cursor.execute("SELECT t.ID,t.SUMMARY,t.STATUS,t.MILESTONE,start.VALUE AS STARTDATE,due.VALUE AS DUEDATE,est.VALUE AS ESTIMATION "+
                       "FROM TICKET t "+
                       "JOIN TICKET_CUSTOM start ON start.TICKET=t.ID AND start.NAME='startdate' "+
                       "JOIN TICKET_CUSTOM due ON due.TICKET=t.ID AND due.NAME='duedate' "+
                       "JOIN TICKET_CUSTOM est ON est.TICKET=t.ID AND est.NAME='estimatedhours' "+
                       "WHERE "+where+" ORDER BY "+orderBy, None)

        view = "<table class='listing tickets'>"
        view += "<thead>"
        view += "<tr>"
        view += "  <th class='id'>Ticket</th>"
        view += "  </th><th class='summary'>Summary</th>"
        view += "  </th><th class='status'>Status</th>"
        view += "  </th><th class='milestone'>Milestone</th>"
        view += "  </th><th class='component'>Scheduled&nbsp;for</th>"
        view += "  </th><th class='component'>Effort</th>"
        view += "</tr>"
        view += "</thead>"
        view += "<tbody>"

        line = "even"

        for t in cursor:
            id = t[0];
            summary = t[1];
            status = t[2];
            milestone = t[3];
            due = self.renderDate(t[5], t[4])
            est = t[6]

            if line=="even":
                line = "odd"
            elif line=="odd":
                line = "even"    

            view += "      <tr class='%s prio1'>" % (line)
            view += "            <td class='id'><a href='%s' title='View ticket'>#%s</a></td>" % (req.href.ticket(id),id)
            view += "            <td class='summary'>"
            view += "              <a href='%s' title='View ticket'>%s</a>" % (req.href.ticket(id),summary)
            view += "            </td>"
            view += "            <td class='status'>%s</td>" % (status)
            view += "            <td class='milestone'>%s</td>" % (milestone)
            view += "            <td class='component'>%s</td>" % (due)
            view += "            <td class='component'>%s</td>" % (est)
            view += "      </tr>\n"

        view += "<tbody>"
        view += "</table>"
        
        cursor.close()
        
        return view
    
    def renderDate(self, d, s):
        dt = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
        day = self.days(dt)
        st = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        started = self.days(st)
        
        weekday = dt.strftime('%w')
        
        if day==0:
            msg = "today"
        elif day==-1:
            msg = "yesterday"
        elif day==+1:
            msg = "tomorrow"
        elif day<-13:
            msg = "%s weeks ago" % (-day/7)
        elif day<-6:
            msg = "the weeks before" 
        elif day<0:
            msg = "%s days ago" % (-day)
        elif day>13:
            msg = "in %s weeks" % (day/7)
        elif day>6:
            msg = "next week"
        elif weekday=='0': 
            msg = "Sunday"
        elif weekday=='1': 
            msg = "Monday"
        elif weekday=='2': 
            msg = "Tuesday"
        elif weekday=='3': 
            msg = "Wednesday"
        elif weekday=='4': 
            msg = "Thursday"
        elif weekday=='5': 
            msg = "Friday"
        elif weekday=='6': 
            msg = "Saturday"
            
        if started<0:
            msg += "<br/>started?"
        elif started==0:
            msg += "<br/>start&nbsp;now!"
            
        return msg 

    def days(self, dt):
        now = datetime.now()
        timedelta = dt-now
        return timedelta.days
        