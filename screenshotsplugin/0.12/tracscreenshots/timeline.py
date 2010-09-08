# -*- coding: utf-8 -*-

# Genshi imports.
from genshi.builder import tag

# Trac imports.
from trac.core import *
from trac.mimeview import Context
from trac.util.datefmt import to_timestamp

# Trac interfaces.
from trac.timeline import ITimelineEventProvider

# Local imports.
from tracscreenshots.api import *
from tracscreenshots.core import _, tag_

class ScreenshotsTimeline(Component):
    """
        The timeline module implements timeline events when new screenshots are
        uploaded.
    """
    implements(ITimelineEventProvider)

    # ITimelineEventProvider

    def get_timeline_filters(self, req):
        if 'SCREENSHOTS_VIEW' in req.perm:
            yield ('screenshots', _("Screenshots changes"))

    def get_timeline_events(self, req, start, stop, filters):
        self.log.debug("start: %s, stop: %s, filters: %s" % (start, stop,
          filters))
        if ('screenshots' in filters) and ('SCREENSHOTS_VIEW' in req.perm):
            # Create context.
            context = Context.from_request(req)('screenshots-timeline')
            db = self.env.get_db_cnx()
            context.cursor = db.cursor()

            # Get API component.
            api = self.env[ScreenshotsApi]

            # Get message events
            for screenshot in api.get_new_screenshots(context, to_timestamp(start),
              to_timestamp(stop)):
                yield ('newticket', screenshot['time'], screenshot['author'],
                  (screenshot['id'], screenshot['name'],
                   screenshot['description']))

    def render_timeline_event(self, context, field, event):
        # Decompose event data.
        id, name, description = event[3]

        # Return apropriate content.
        if field == 'url':
           return context.href.screenshots(id)
        elif field == 'title':
           return tag_("New screenshot %(name)s created", name = tag.em(name))
        elif field == 'description':
           return tag(description)
