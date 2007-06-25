import re
import dbhelper
from trac.log import logger_factory
from trac.core import *
from trac.web import IRequestHandler
from trac.util import Markup
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

        def produce(user,ticket,time,state,summary):
            kind = 'workstop'
            humankind = 'stopped'
            if state == 1:
                kind = 'workstart'
                humankind = 'started'
            ticket_href = href.ticket(ticket)
            if format == 'rss':
                title = '%s %s working on Ticket #%s: %s' % \
                        (user, humankind, ticket, summary)
            else:
                title = Markup('%s %s working on Ticket <em title="%s">#%s</em>' % \
                               (user, humankind, summary, ticket))
            message = ''
            return kind, ticket_href, title, time, user, message

        # Ticket changes
        if 'worklog' in filters:
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            cursor.execute("SELECT wl.user,wl.ticket,wl.time,wl.state,t.summary"
                           "  FROM work_log wl "
                           "    INNER JOIN ticket t ON t.id = wl.ticket "
                           "      AND wl.time>=%s AND wl.time<=%s "
                           "ORDER BY wl.time"
                           % (start, stop))
            previous_update = None
            for user,ticket,time,state,summary in cursor:
                ev = produce(user,ticket,time,state,summary)
                if ev:
                    yield ev

