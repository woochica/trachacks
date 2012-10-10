# -*- coding: utf-8 -*-

from genshi.builder import tag

from trac.core import *
from trac.mimeview import Context
from trac.util.text import pretty_size
from trac.wiki.formatter import format_to_oneliner
from trac.util.datefmt import to_timestamp

from trac.timeline import ITimelineEventProvider

from tracdownloads.api import *

class DownloadsTimeline(Component):
    """
        The timeline module implements timeline events when new downloads are
        inserted.
    """
    implements(ITimelineEventProvider)

    # ITimelineEventProvider

    def get_timeline_filters(self, req):
        if 'DOWNLOADS_VIEW' in req.perm:
            yield ('downloads', 'Downloads changes')

    def get_timeline_events(self, req, start, stop, filters):
        self.log.debug("start: %s, stop: %s, filters: %s" % (start, stop,
          filters))
        if ('downloads' in filters) and ('DOWNLOADS_VIEW' in req.perm):
            # Create context.
            context = Context.from_request(req)('downloads-timeline')
            db = self.env.get_db_cnx()
            context.cursor = db.cursor()

            # Get API component.
            api = self.env[DownloadsApi]

            # Get message events
            for download in api.get_new_downloads(context, to_timestamp(start),
              to_timestamp(stop)):
                yield ('newticket', download['time'], download['author'],
                  (download['id'], download['file'], download['description'],
                  download['size']))

    def render_timeline_event(self, context, field, event):
        # Decompose event data.
        id, name, description, size = event[3]

        # Return apropriate content.
        if field == 'url':
           return context.req.href.downloads(id)
        elif field == 'title':
           return tag('New download ', tag.em(name), ' created')
        elif field == 'description':
           return tag('(%s) ' % (pretty_size(size),), format_to_oneliner(
             self.env, context, description))
