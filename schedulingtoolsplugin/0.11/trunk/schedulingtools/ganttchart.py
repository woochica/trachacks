from datetime import datetime, timedelta
import time

from trac.util.html import Markup
from trac.wiki.macros import WikiMacroBase


class GanttChart(WikiMacroBase):
    
    def render_macro(self, req, name, content):
        
        view = self.render(req)
        
        return Markup(view)

    def render(self, req):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        where = "t.STATUS<>'closed' AND t.STATUS<>'resolved'";
        orderBy = "t.MILESTONE ASC,start.VALUE ASC";
        cursor.execute("SELECT t.ID,t.SUMMARY,t.STATUS,t.OWNER,t.MILESTONE,start.VALUE AS STARTDATE,due.VALUE AS DUEDATE "+
                       "FROM TICKET t "+
                       "JOIN TICKET_CUSTOM start ON start.TICKET=t.ID AND start.NAME='startdate' "+
                       "JOIN TICKET_CUSTOM due ON due.TICKET=t.ID AND due.NAME='duedate' "+
                       "WHERE "+where+" ORDER BY "+orderBy, None)

        width = 800
        tmin = self.timestamp("2010-01-01 00:00:00")
        tmax = self.timestamp("2000-01-01 00:00:00")

        tickets = []
        for t in cursor:
            ticket = {}
            ticket['id'] = t[0];
            ticket['summary'] = t[1];
            ticket['status'] = t[2];
            ticket['owner'] = t[3];
            ticket['milestone'] = t[4];
            ticket['start'] = self.timestamp(t[5])
            ticket['due'] = self.timestamp(t[6])
            
            tmin = min(tmin,ticket['start'])
            tmax = max(tmax,ticket['due'])
            
            tickets.append(ticket)

        cursor.close()

        view = "<TABLE cellspacing='0' cellpadding='0' WIDTH='100%' style='position:relative;padding:0px;border:1px solid black'>"

        days = int(tmax-tmin)/(60*60*24)
        incr = timedelta(days=1)
        format = "%d"
        if days>14:
            incr = timedelta(days=7)
            format = "%d.%m."
            
        mark = datetime.utcfromtimestamp((int(tmin)/(60*60*24))*60*60*24)
        mark += incr
        percent = 0;
        view += "<TR><td style='height: 15px; background-color:#DDDDDD'>"
        while percent<100:
            percent = (time.mktime(mark.timetuple())-tmin)/(tmax-tmin)*100
            view += "<div style='position:absolute;left:%s%%;width:1px;height:100%%;top:0px;background-color:black'></div>\n" % (percent)
            view += "<div style='position:absolute;left:%s%%;top:0px'> %s</div>\n" % (percent, mark.strftime(format))
            mark += incr;

        percent = (time.mktime(datetime.now().timetuple())-tmin)/(tmax-tmin)*100
        view += "<div style='position:absolute;left:%s%%;width:1px;height:100%%;top:0px;background-color:red'></div>\n" % (percent)
        view += "</td></TR>"

        line = "#EEEEEE"

        for t in tickets:


            # view += "<TR><TD>%s</TD><TD>%s</TD><TD>%s</TD><TD>%s</TD><TD>%s</TD><TD>%s</TD></TR>" % (id,summary,owner,milestone,startdate,duedate)
            
            start = (t['start']-tmin)/(tmax-tmin)*100
            due = (t['due']-tmin)/(tmax-tmin)*100

            if line=="#FFFFFF":
                line = "#EEEEEE"
            elif line=="#EEEEEE":
                line = "#FFFFFF"    

            view += "<TR><TD style='height: 17px; background-color:%s'>" % (line)
            view += "<div style='position:relative;left:%s%%;width:%s%%;height:15px;background-color:blue'/>" % (start,due-start)
            view += "<div style='position:relative;left:%s%%;height:15px;width:200px'>&nbsp;<a href='%s' title='%s'>%s<a> %s</div>" % (100,req.href.ticket(t['id']),t['summary'],t['id'],t['owner'])
            view += "</TD></TR>"
            
        view += "</TABLE>"

        return view
                
    def timestamp(self, d):
        dt = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
        return time.mktime(dt.timetuple())