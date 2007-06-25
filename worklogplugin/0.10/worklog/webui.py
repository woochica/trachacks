import re
import dbhelper
from time import time
from datetime import tzinfo, timedelta, datetime
from usermanual import *
from trac.log import logger_factory
from trac.core import *
from trac.web import IRequestHandler
from trac.util.datefmt import format_date, format_time
from trac.util import Markup
from trac.ticket import Ticket
from trac.web.chrome import add_stylesheet, add_script, \
     INavigationContributor, ITemplateProvider
from trac.web.href import Href


class WorkLogPage(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    def __init__(self):
        pass

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if re.search('/worklog', req.path_info):
            return "worklog"
        else:
            return ""

    def get_navigation_items(self, req):
        url = req.href.worklog()
        if req.perm.has_permission("REPORT_VIEW"):
            yield 'mainnav', "worklog", \
                  Markup('<a href="%s">%s</a>' % \
                         (url , "Work Log"))

    # Stolen from Trac trunk :)
    def pretty_timedelta(self, time1, time2=None, resolution=None):
        """Calculate time delta (inaccurately, only for decorative purposes ;-) for
        prettyprinting. If time1 is None, the current time is used."""
        if not time1: time1 = datetime.now()
        if not time2: time2 = datetime.now()
        if time1 > time2:
            time2, time1 = time1, time2
        units = ((3600 * 24 * 365, 'year',   'years'),
                 (3600 * 24 * 30,  'month',  'months'),
                 (3600 * 24 * 7,   'week',   'weeks'),
                 (3600 * 24,       'day',    'days'),
                 (3600,            'hour',   'hours'),
                 (60,              'minute', 'minutes'))
        diff = time2 - time1
        age_s = int(diff.days * 86400 + diff.seconds)
        if resolution and age_s < resolution:
            return ''
        if age_s < 60:
            return '%i second%s' % (age_s, age_s != 1 and 's' or '')
        for u, unit, unit_plural in units:
            r = float(age_s) / float(u)
            if r >= 0.9:
                r = int(round(r))
                return '%d %s' % (r, r == 1 and unit or unit_plural)
        return ''

    # IRequestHandler methods
    def get_worklog(self, req):
        sql = "SELECT sid,value FROM session_attribute WHERE name='name'"
        users = dbhelper.get_all(self.env.get_db_cnx(), sql)[1]
        usermap = {}
        for (user, name) in users:
            usermap[user] = name

        sql = "CREATE TEMPORARY TABLE work_log_tmp (user text, lastchange integer)"
        dbhelper.execute_non_query(self.env.get_db_cnx(), sql)
        
        sql = "INSERT INTO work_log_tmp SELECT user,MAX(lastchange) FROM work_log GROUP BY user"
        dbhelper.execute_non_query(self.env.get_db_cnx(), sql)

        sql = """
        SELECT wl.user, wl.starttime, wl.endtime, wl.ticket, t.summary
        FROM work_log_tmp wlt
        LEFT JOIN work_log wl ON wlt.user=wl.user AND wlt.lastchange=wl.lastchange
        LEFT JOIN ticket t ON wl.ticket=t.id
        """
        worklog = dbhelper.get_all(self.env.get_db_cnx(), sql)[1]
        log = {}
        for user in usermap.keys():
            log[user] = { "user": user,
                          "name": usermap[user]
                          }
        if not worklog:
            return log
        
        for (user,starttime,endtime,ticket,summary) in worklog:
            started = datetime.fromtimestamp(starttime)

            log[user] = { "user": user,
                          "name": usermap[user],
                          "ticket": ticket,
                          "ticket_url": req.href.ticket(ticket),
                          "summary": summary,
                          "started": started,
                          "delta": 'Started ' + format_date(starttime) + " " + format_time(starttime) + \
                                   " (" + self.pretty_timedelta(started) + " ago)"
                          }

            if not endtime == 0:
                finished = datetime.fromtimestamp(endtime)
                log[user]["finished"] = finished
                log[user]["delta"] = 'Worked on from ' + format_date(starttime) + " " + format_time(starttime) + " - " + format_date(endtime) + " " + format_time(endtime) + \
                                   " (" + self.pretty_timedelta(started, finished) + ")"

                
        return log
        
    def match_request(self, req):
        if re.search('/worklog', req.path_info):
            return True
        return None

    def process_request(self, req):
        messages = []

        def addMessage(s):
            messages.extend([s]);

        def start_work(authname, ticket):
            tckt = Ticket(self.env, ticket)
            tckt_link = Markup('<a href="%s" title="%s">%s</a>' % \
                         (req.href.ticket(ticket), tckt['summary'], "#" + ticket))
            tckt_link = Markup('#' + ticket)

            sql = "SELECT MAX(lastchange) FROM work_log WHERE user='%s'" % (authname)
            lastchange = dbhelper.get_scalar(self.env.get_db_cnx(), sql)
            if lastchange:
                sql = "SELECT endtime FROM work_log WHERE user='%s' AND lastchange=%s" % (authname, lastchange)
                endtime = dbhelper.get_scalar(self.env.get_db_cnx(), sql)
                if endtime == 0:
                    addMessage("You cannot work on ticket " + tckt_link + " as you seem to already be working on another ticket.")
                    return
            
            if not authname == tckt['owner']:
                addMessage("You cannot work on ticket " + tckt_link + " as you are not the owner.")
                return

            if "closed" == tckt['status']:
                addMessage("You cannot work on ticket " + tckt_link + " as it is currently in a closed state.")
                return
            
            # Add a comment here if we are gonna do that.
            now = int(time())
            sql = "INSERT INTO work_log (user, ticket, lastchange, starttime, endtime) VALUES ('%s', %s, %s, %s, %s)" % \
                  (authname, ticket, now, now, 0)
            dbhelper.execute_non_query(self.env.get_db_cnx(), sql)
            addMessage("You are now working on ticket " + tckt_link + ".")

        def stop_work(authname, ticket):
            tckt = Ticket(self.env, ticket)
            tckt_link = Markup('<a href="%s" title="%s">%s</a>' % \
                         (req.href.ticket(ticket), tckt['summary'], "#" + ticket))
            tckt_link = Markup('#' + ticket)

            sql = "SELECT MAX(lastchange) FROM work_log WHERE user='%s'" % (authname)
            lastchange = dbhelper.get_scalar(self.env.get_db_cnx(), sql)
            if not lastchange:
                addMessage("You cannot stop working on ticket " + tckt_link + " as it apears you've not started working on anything yet!")
                return
            
            sql = "SELECT ticket,endtime FROM work_log WHERE user='%s' AND lastchange=%s" % (authname, lastchange)
            data = dbhelper.get_all(self.env.get_db_cnx(), sql)[1]
            if not data:
                addMessage("You cannot stop working on ticket " + tckt_link + " as it appears you've not started working on it yet!")
                return
            for (activeticket, endtime) in data:
                if not activeticket == int(ticket):
                    addMessage("You cannot stop working on ticket " + tckt_link + " as it appears you've not started working on it yet! " + str(activeticket) + " " + str(endtime))
                    return
                if not endtime == 0:
                    addMessage("You cannot stop working on ticket " + tckt_link + " as it apears you've already finished working!")
                    return
            
            # Here we should calculate times and automatically add hours to ticket etc.
            now = int(time());
            sql = "UPDATE work_log SET endtime=%s, lastchange=%s WHERE user='%s' AND lastchange=%s AND endtime=0" % \
                  (now, now, authname, lastchange)
            dbhelper.execute_non_query(self.env.get_db_cnx(), sql)
            addMessage("You are no longer working on ticket " + tckt_link + ".")
            
        if not re.search('/worklog', req.path_info):
            return None


        if req.method == 'POST':
            if req.args.has_key('startwork') and req.args.has_key('ticket'):
                start_work(req.authname, req.args["ticket"])
            elif req.args.has_key('stopwork') and req.args.has_key('ticket'):
                stop_work(req.authname, req.args["ticket"])
                
        req.hdf["worklog"] = {"messages": messages,
                              "worklog": self.get_worklog(req),
                              "href":req.href.worklog(),
                              "usermanual_href":req.href.wiki(user_manual_wiki_title),
                              "usermanual_title":user_manual_title
                             }
        add_stylesheet(req, "worklog/worklogplugin.css")
        add_script(req, "worklog/linkifyer.js")
        return 'worklog.cs', 'text/html'
        
        
    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('worklog', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
