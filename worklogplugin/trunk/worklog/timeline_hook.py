# -*- coding: utf-8 -*-

import re
from genshi.builder import tag
from util import *
from trac.log import logger_factory
from trac.core import *
from trac.util.datefmt import to_timestamp, utc
from trac.util.text import shorten_line
from trac.ticket.api import TicketSystem
from trac.timeline.api import ITimelineEventProvider
from trac.wiki.formatter import format_to_oneliner
from trac.resource import Resource, get_resource_url, \
                         render_resource_link, get_resource_shortname, \
                         get_resource_name
from trac.web.chrome import add_stylesheet

class WorkLogTimelineAddon(Component):
    implements(ITimelineEventProvider)
    
    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if req.perm.has_permission('WORK_VIEW'):
            yield ('workstart', 'Work started', True)
            yield ('workstop', 'Work stopped', True)

    def get_timeline_events(self, req, start, stop, filters):
        # Worklog changes
        show_starts = 'workstart' in filters
        show_stops = 'workstop' in filters
        if show_starts or show_stops:
            add_stylesheet(req, "worklog/worklogplugin.css")
            
            ts_start = to_timestamp(start)
            ts_stop = to_timestamp(stop)

            ticket_realm = Resource('ticket')
            db = self.env.get_read_db()
            cursor = db.cursor()

            cursor.execute("""SELECT wl.worker,wl.ticket,wl.time,wl.starttime,wl.comment,wl.kind,t.summary,t.status,t.resolution,t.type
                             FROM (
                             
                             SELECT worker, ticket, starttime AS time, starttime, comment, 'start' AS kind
                             FROM work_log

                             UNION

                             SELECT worker, ticket, endtime AS time, starttime, comment, 'stop' AS kind
                             FROM work_log

                             ) AS wl
                             INNER JOIN ticket t ON t.id = wl.ticket 
                                 AND wl.time>=%s AND wl.time<=%s 
                           ORDER BY wl.time"""
                           % (ts_start, ts_stop))
            previous_update = None
            for worker,tid,ts,ts_start,comment,kind,summary,status,resolution,type in cursor:
                ticket = ticket_realm(id=tid)
                time = datetime.fromtimestamp(ts, utc)
                started = None
                if kind == 'start':
                    if not show_starts:
                        continue
                    yield ('workstart', time, worker, (ticket,summary,status,resolution,type, started, ""))
                else:
                    if not show_stops:
                        continue
                    started = datetime.fromtimestamp(ts_start, utc)
                    if comment:
                        comment = "(Time spent: %s)[[BR]]%s" % (pretty_timedelta(started, time), comment)
                    else:
                        comment = '(Time spent: %s)' % pretty_timedelta(started, time)
                    yield ('workstop', time, worker, (ticket,summary,status,resolution,type, started, comment))
    
    def render_timeline_event(self, context, field, event):
        ticket,summary,status,resolution,type, started, comment = event[3]
        if field == 'url':
            return context.href.ticket(ticket.id)
        elif field == 'title':
            title = TicketSystem(self.env).format_summary(summary, status,
                                                          resolution, type)
            return tag('Work ', started and 'stopped' or 'started',
                       ' on Ticket ', tag.em('#', ticket.id, title=title),
                       ' (', shorten_line(summary), ') ')
        elif field == 'description':
            if self.config['timeline'].getbool('abbreviated_messages'):
                comment = shorten_line(comment)
            markup = format_to_oneliner(self.env, context(resource=ticket),
                                        comment)
            #if wiki_page.version > 1:
            #    diff_href = context.href.wiki(
            #        wiki_page.id, version=wiki_page.version, action='diff')
            #    markup = tag(markup, ' ', tag.a('(diff)', href=diff_href))
            return markup


