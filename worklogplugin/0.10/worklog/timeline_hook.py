import re
from util import *
from trac.log import logger_factory
from trac.core import *
from trac.web import IRequestHandler
from trac.util import Markup
from trac.web.chrome import add_stylesheet
from trac.web.href import Href
from trac.Timeline import ITimelineEventProvider
from trac.wiki.formatter import wiki_to_html, wiki_to_oneliner

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

            cursor.execute("""SELECT wl.user,wl.ticket,wl.time,wl.starttime,wl.comment,wl.kind,wl.humankind,t.summary,t.status
                             FROM (
                             
                             SELECT user, ticket, starttime AS time, starttime, comment, 'workstart' AS kind, 'started' AS humankind
                             FROM work_log

                             UNION

                             SELECT user, ticket, endtime AS time, starttime, comment, 'workstop' AS kind, 'stopped' AS humankind
                             FROM work_log

                             ) AS wl
                             INNER JOIN ticket t ON t.id = wl.ticket 
                                 AND wl.time>=%s AND wl.time<=%s 
                           ORDER BY wl.time"""
                           % (start, stop))
            previous_update = None
            for user,ticket,time,starttime,comment,kind,humankind,summary,status in cursor:
                summary = Markup.escape(summary)
                time = float(time)
                starttime = float(starttime)
                if format == 'rss':
                    title = Markup('%s %s working on Ticket #%s (%s): %s' % \
                                   (user, humankind, ticket, summary, comment))
                else:
                    title = Markup('%s %s working on Ticket <em title="%s">#%s</em>' % \
                                   (user, humankind, summary, ticket))
                message = ''
                if kind == 'workstop':
                    started = datetime.fromtimestamp(starttime)
                    finished = datetime.fromtimestamp(time)
                    if comment:
                        message = wiki_to_oneliner(comment, self.env, db, shorten=True) + Markup('<br />(Time spent: %s)' % pretty_timedelta(started, finished))
                    else:
                        message = 'Time spent: %s' % pretty_timedelta(started, finished)
                yield kind, href.ticket(ticket), title, time, user, message


