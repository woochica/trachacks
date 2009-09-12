from datetime import datetime, timedelta
import time

from trac.util.html import Markup
from trac.wiki.macros import WikiMacroBase



class GanttChart(WikiMacroBase):
    
    def render_macro(self, req, name, content):
        
        self.view = ""
        
        self.render(req)
        
        return Markup(self.view)

    def init(self, req):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        where = "t.STATUS<>'closed' AND t.STATUS<>'resolved'";
        if "owner" in req.args:
            where += " AND t.OWNER='%s'"%(req.args['owner'])
        if "milestone" in req.args:
            where += " AND t.MILESTONE='%s'"%(req.args['milestone'])
        orderBy = "m.due ASC,start.VALUE ASC";
        cursor.execute("SELECT t.ID,t.SUMMARY,t.STATUS,t.OWNER,t.MILESTONE,start.VALUE AS STARTDATE,due.VALUE AS DUEDATE,m.DUE "+
                       "FROM TICKET t "+
                       "JOIN TICKET_CUSTOM start ON start.TICKET=t.ID AND start.NAME='startdate' "+
                       "JOIN TICKET_CUSTOM due ON due.TICKET=t.ID AND due.NAME='duedate' "+
                       "JOIN MILESTONE m ON m.NAME=t.MILESTONE "+
                       "WHERE "+where+" ORDER BY "+orderBy, None)

        milestone = {'name':None}

        self.tmin = self.timestamp("2010-01-01 00:00:00")
        self.tmax = self.timestamp("2000-01-01 00:00:00")
        self.milestones = []
        self.tickets = []
        for t in cursor:
            
            ticket = {}
            ticket['id'] = t[0];
            ticket['summary'] = t[1];
            ticket['status'] = t[2];
            ticket['owner'] = t[3];
            ticket['milestone'] = t[4];
            ticket['start'] = self.timestamp(t[5])
            ticket['due'] = self.timestamp(t[6])

            if milestone['name']!=ticket['milestone']:
                milestone = {}
                milestone['name'] = ticket['milestone']
                milestone['due'] = t[7]
                milestone['tmin'] = self.timestamp("2010-01-01 00:00:00")
                milestone['tmax'] = self.timestamp("2000-01-01 00:00:00")
                self.milestones.append(milestone)
            
            milestone['tmin'] = min(milestone['tmin'],ticket['start'])
            milestone['tmax'] = max(milestone['tmax'],ticket['due'])
            self.tmin = min(self.tmin,ticket['start'])
            self.tmax = max(self.tmax,ticket['due'])
            
            self.tickets.append(ticket)

        cursor.close()
        self.line = "#EEEEEE"

    def render(self, req):
        self.init(req)

        self.view = ""
        if self.tmin>=self.tmax:
            return self.view

        self.view += "<TABLE cellspacing='0' cellpadding='0' WIDTH='100%' style='position:relative;padding:0px;border:1px solid black'>"

        self.renderScale()

        milestone = {'name':None}
        for t in self.tickets:

            if t['milestone']!=milestone['name']:
                milestone = self.milestones.pop(0)
                color = "black";
                if milestone['due']<milestone['tmax']:
                    color = "red"
                due = datetime.utcfromtimestamp(milestone['tmax']).strftime("%d.%m.")
                self.renderLine(milestone['tmin'], milestone['tmax'], color, "<a href='%s'>%s<a> %s" % (req.href.milestone(milestone['name']),milestone['name'],due))
                
            self.renderLine(t['start'], t['due'], "blue", "<a href='%s' title='%s'>%s<a> %s" % (req.href.ticket(t['id']),t['summary'],t['id'],t['owner']))
            
        self.view += "</TABLE>"

        return self.view
    
    def renderScale(self):
        days = int(self.tmax-self.tmin)/(60*60*24)
        incr = timedelta(days=1)
        format = "%d"
        weekend = 0.1*100/days
        offset = 0
        mark = datetime.utcfromtimestamp((int(self.tmin)/(60*60*24))*60*60*24)

        if days>14:
            incr = timedelta(days=7)
            format = "%d.%m."
            weekend = 2*100/days
            offset = 6-mark.weekday()
            if offset<0: 
                offset += 7
            
        mark += timedelta(days=offset)
        mark += incr
        percent = self.percent(time.mktime(mark.timetuple()))
        self.view += "<TR><td style='height: 15px; background-color:#DDDDDD'>"
        while percent<100:
            self.view += "<div style='position:absolute;left:%s%%;width:%s%%;height:100%%;top:0px;background-color:#DDDDEE'></div>\n" % (percent,weekend)
            self.view += "<div style='position:absolute;left:%s%%;top:0px'> %s</div>\n" % (percent, mark.strftime(format))
            mark += incr;
            percent = self.percent(time.mktime(mark.timetuple()))

        percent = self.percent(time.mktime(datetime.now().timetuple()))
        self.view += "<div style='position:absolute;left:%s%%;width:3px;height:100%%;top:0px;background-color:green'></div>\n" % (percent)
        self.view += "</td></TR>"
    
    def percent(self, timestamp):
        return (timestamp-self.tmin)/(self.tmax-self.tmin)*100
    
    def renderLine(self, mmin, mmax, color, label):
        start = self.percent(mmin)    
        end = self.percent(mmax)    
        if self.line=="#FFFFFF":
            self.line = "#EEEEEE"
        elif self.line=="#EEEEEE":
            self.line = "#FFFFFF"    
        self.view += "<TR><TD style='height: 17px; background-color:%s'>" % (self.line)
        self.view += "<div style='position:relative;left:%s%%;width:%s%%;height:15px;background-color:%s'/>" % (start,end-start,color)
        self.view += "<div style='position:relative;left:100%%;height:15px;width:200px'>&nbsp;%s </div>" % (label)
        self.view += "</TD></TR>"
                
    def timestamp(self, d):
        dt = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
        return time.mktime(dt.timetuple())
    