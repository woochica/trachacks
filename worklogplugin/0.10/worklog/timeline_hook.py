import re
from util import *
from trac.log import logger_factory
from trac.core import *
from trac.web import IRequestHandler
from trac.util import Markup
from trac.web.chrome import add_stylesheet
from trac.web.href import Href
from trac.Timeline import ITimelineEventProvider

class WorkLogTimelineAddon(Component):
    implements(ITimelineEventProvider)
    
    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        yield ('worklog', 'Work Log changes')

    def get_timeline_events(self, req, start, stop, filters):
        format = req.args.get('format')

        href = format == 'rss' and req.abs_href or req.href

        # Ticket changes
        if 'worklog' in filters:
            add_stylesheet(req, "worklog/worklogplugin.css")
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            cursor.execute("""SELECT wl.user,wl.ticket,wl.time,wl.starttime,wl.kind,wl.humankind,t.summary
                             FROM (
                             
                             SELECT user, ticket, starttime AS time, starttime, 'workstart' AS kind, 'started' AS humankind
                             FROM work_log

                             UNION

                             SELECT user, ticket, endtime AS time, starttime, 'workstop' AS kind, 'stopped' AS humankind
                             FROM work_log

                             ) AS wl
                             INNER JOIN ticket t ON t.id = wl.ticket 
                                 AND wl.time>=%s AND wl.time<=%s 
                           ORDER BY wl.time"""
                           % (start, stop))
            previous_update = None
            for user,ticket,time,starttime,kind,humankind,summary in cursor:
                ticket_href = href.ticket(ticket)
                if format == 'rss':
                    title = '%s %s working on Ticket #%s: %s' % \
                            (user, humankind, ticket, summary)
                else:
                    title = Markup('%s %s working on Ticket <em title="%s">#%s</em>' % \
                                   (user, humankind, summary, ticket))
                message = ''
                if kind == 'workstop':
                    started = datetime.fromtimestamp(starttime)
                    finished = datetime.fromtimestamp(time)
                    message = 'Time spent: ~' + pretty_timedelta(started, finished, True)
                yield kind, ticket_href, title, time, user, message


