import re
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
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT wl.user, s.value, wl.starttime, wl.endtime, wl.ticket, t.summary '
                       'FROM (SELECT user,MAX(lastchange) lastchange FROM work_log GROUP BY user) wlt '
                       'LEFT JOIN work_log wl ON wlt.user=wl.user AND wlt.lastchange=wl.lastchange '
                       'LEFT JOIN ticket t ON wl.ticket=t.id '
                       'LEFT JOIN session_attribute s ON wl.user=s.sid AND s.name=\'name\' '
                       'ORDER BY wl.lastchange DESC, wl.user')

        log = {}
        for (user,name,starttime,endtime,ticket,summary) in cursor:
            started = datetime.fromtimestamp(starttime)

            dispname = user
            if name:
                dispname = '%s (%s)' % (name, user)
            log[user] = { "name": dispname,
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

        if not re.search('/worklog', req.path_info):
            return None

        if req.method == 'POST':
            mgr = WorkLogManager(self.env, self.config, req.authname)
            if req.args.has_key('startwork') and req.args.has_key('ticket'):
                if not mgr.start_work(req.args['ticket']):
                    addMessage(mgr.get_explanation())
                else:
                    addMessage('You are now working on ticket #%s.' % (req.args['ticket'],))
            elif req.args.has_key('stopwork'):
                stoptime = None
                if req.args.has_key('stoptime'):
                    stoptime = int(req.args['stoptime'])
                if not mgr.stop_work(stoptime):
                    addMessage(mgr.get_explanation())
                else:
                    addMessage('You have stopped working.')
        
        req.hdf["worklog"] = {"messages": messages,
                              "worklog": self.get_worklog(req),
                              "href":req.href.worklog(),
                              "usermanual_href":req.href.wiki(user_manual_wiki_title),
                              "usermanual_title":user_manual_title
                             }
        add_stylesheet(req, "worklog/worklogplugin.css")
        return 'worklog.cs', None
        
        
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
    
