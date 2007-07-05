import re
import dbhelper
from util import *
from time import time
from datetime import tzinfo, timedelta, datetime
from usermanual import *
from manager import WorkLogManager
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

    # IRequestHandler methods
    def get_worklog(self, req):
        sql = "SELECT sid,value FROM session_attribute WHERE name='name'"
        users = dbhelper.get_all(self.env.get_db_cnx(), sql)[1]
        usermap = {}
        for (user, name) in users:
            usermap[user] = name

        sql = """
        SELECT wl.user, wl.starttime, wl.endtime, wl.ticket, t.summary
        FROM (SELECT user,MAX(lastchange) lastchange FROM work_log GROUP BY user) wlt
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
                                   " (" + pretty_timedelta(started) + " ago)"
                          }

            if not endtime == 0:
                finished = datetime.fromtimestamp(endtime)
                log[user]["finished"] = finished
                log[user]["delta"] = 'Worked on from ' + format_date(starttime) + " " + format_time(starttime) + " - " + format_date(endtime) + " " + format_time(endtime) + \
                                   " (" + pretty_timedelta(started, finished) + ")"

                
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
            tckt_link = '#' + ticket

            mgr = WorkLogManager(self.env, self.config, req.authname)
            if not mgr.can_work_on(ticket):
                addMessage(mgr.get_explanation())
                return
            
            # Add a comment here if we are gonna do that.
            now = int(time())
            sql = "INSERT INTO work_log (user, ticket, lastchange, starttime, endtime) VALUES ('%s', %s, %s, %s, %s)" % \
                  (authname, ticket, now, now, 0)
            db = self.env.get_db_cnx();
            cursor = db.cursor()
            cursor.execute(sql)
            addMessage("You are now working on ticket " + tckt_link + ".")

        def stop_work(authname, ticket):
            tckt = Ticket(self.env, ticket)
            tckt_link = Markup('<a href="%s" title="%s">%s</a>' % \
                         (req.href.ticket(ticket), tckt['summary'], "#" + ticket))
            tckt_link = Markup('#' + ticket)

            task = get_latest_task(self.env.get_db_cnx(), authname)
            if not task:
                addMessage("You cannot stop working on ticket " + tckt_link + " as it apears you've not started working on anything yet!")
                return
            
            if not task['endtime'] == 0:
                addMessage("You cannot stop working on ticket " + tckt_link + " as it appears you've not started working on it yet!")
                return
            if not task['ticket'] == int(ticket):
                addMessage("You cannot stop working on ticket " + tckt_link + " as it appears you're working on something else!")
                return
            
            # Here we should calculate times and automatically add hours to ticket etc.
            now = int(time());
            sql = "UPDATE work_log SET endtime=%s, lastchange=%s WHERE user='%s' AND lastchange=%s AND endtime=0" % \
                  (now, now, authname, task['lastchange'])
            db = self.env.get_db_cnx();
            cursor = db.cursor()
            cursor.execute(sql)
            addMessage("You are no longer working on ticket " + tckt_link + ".")
            
        if not re.search('/worklog', req.path_info):
            return None


        if req.method == 'POST' and req.args.has_key('ticket'):
            if req.args.has_key('startwork'):
                start_work(req.authname, req.args["ticket"])
            elif req.args.has_key('stopwork'):
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
    
