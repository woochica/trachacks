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
from trac.wiki.formatter import wiki_to_html
from trac.util.text import CRLF

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

    # Internal Methods
    def get_worklog(self, req):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT wl.user, s.value, wl.starttime, wl.endtime, wl.ticket, wl.comment, t.summary '
                       'FROM (SELECT user,MAX(lastchange) lastchange FROM work_log GROUP BY user) wlt '
                       'LEFT JOIN work_log wl ON wlt.user=wl.user AND wlt.lastchange=wl.lastchange '
                       'LEFT JOIN ticket t ON wl.ticket=t.id '
                       'LEFT JOIN session_attribute s ON wl.user=s.sid AND s.name=\'name\' '
                       'ORDER BY wl.lastchange DESC, wl.user')

        log = {}
        for (user,name,starttime,endtime,ticket,comment,summary) in cursor:
            starttime = float(starttime)
            endtime = float(endtime)
            
            started = datetime.fromtimestamp(starttime)

            dispname = user
            if name:
                dispname = '%s (%s)' % (name, user)
                        
            finished = ''
            delta = ''
            if not endtime == 0:
                finished = datetime.fromtimestamp(endtime)
                delta = 'Worked for %s (between %s %s and %s %s)' % \
                        (pretty_timedelta(started, finished),
                         format_date(starttime), format_time(starttime),
                         format_date(endtime), format_time(endtime))
            else:
                delta = 'Started %s ago (%s %s)' % \
                        (pretty_timedelta(started),
                         format_date(starttime), format_time(starttime))
                         

            minutes_elapsed = 0
            if endtime == 0:
                minutes_elapsed = int((int(time()) - starttime) / 60)
            else:
                minutes_elapsed = int((endtime - starttime) / 60)
                
            log[user] = { "name": dispname,
                          "ticket": ticket,
                          "ticket_url": req.href.ticket(ticket),
                          "comment": wiki_to_html(comment, self.env, req),
                          "summary": summary,
                          "started": started,
                          "delta": delta,
                          "finished": finished,
                          "minutes_elapsed": minutes_elapsed
                          }
                
        return log

    def worklog_csv(self, req):
        # Headers
        sep=','
        req.write(sep.join(['user',
                            'full_name',
                            'starttime',
                            'endtime',
                            'ticket',
                            'ticket_summary',
                            'work_comment']) + CRLF)

        # Rows
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT wl.user, s.value, wl.starttime, wl.endtime, wl.ticket, t.summary, wl.comment '
                       'FROM work_log wl '
                       'LEFT JOIN ticket t ON wl.ticket=t.id '
                       'LEFT JOIN session_attribute s ON wl.user=s.sid AND s.name=\'name\' '
                       'ORDER BY wl.lastchange DESC, wl.user')

        for row in cursor:
            req.write(sep.join([str(item)
                                .replace(sep, '_').replace('\\', '\\\\')
                                .replace('\n', '\\n').replace('\r', '\\r')
                                for item in row]) + CRLF)

                
    # IRequestHandler methods
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

        if req.args.has_key('format') and req.args['format'] == 'csv':
            req.send_header('Content-Type', 'text/csv;charset=utf-8')
            self.worklog_csv(req)
            return None

        if req.method == 'POST':
            mgr = WorkLogManager(self.env, self.config, req.authname)
            if req.args.has_key('startwork') and req.args.has_key('ticket'):
                if not mgr.start_work(req.args['ticket']):
                    addMessage(mgr.get_explanation())
                else:
                    addMessage('You are now working on ticket #%s.' % (req.args['ticket'],))
                
                req.redirect(req.args['source_url'])
                return None
                
            elif req.args.has_key('stopwork'):
                stoptime = None
                if req.args.has_key('stoptime'):
                    stoptime = int(req.args['stoptime'])

                comment = ''
                if req.args.has_key('comment'):
                    comment = str(req.args['comment'])

                if not mgr.stop_work(stoptime, comment):
                    addMessage(mgr.get_explanation())
                else:
                    addMessage('You have stopped working.')
                
                req.redirect(req.args['source_url'])
                return None
        
        # no POST, so they're just wanting a list of the worklog entries
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
    
