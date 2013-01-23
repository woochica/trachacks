# -*- coding: utf-8 -*-

# Trac imports.
from trac.core import *
from trac.mimeview import Context
from trac.web.chrome import add_stylesheet
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util.datefmt import to_timestamp, to_datetime, utc
from trac.util.text import to_unicode

# Trac interfaces.
from trac.timeline import ITimelineEventProvider

# Genshi imports.
from genshi.builder import tag

# Local imports.
from tracdiscussion.api import *

class DiscussionTimeline(Component):
    """
        The timeline module implements raising timeline events when
        forums, topics and messages are changed.
    """
    implements(ITimelineEventProvider)

    # ITimelineEventProvider

    def get_timeline_filters(self, req):
        if 'DISCUSSION_VIEW' in req.perm:
            yield ('discussion', self.config.get('discussion', 'title') +
              ' changes')

    def get_timeline_events(self, req, start, stop, filters):
        self.log.debug("start: %s, stop: %s, filters: %s" % (start, stop,
          filters))

        if ('discussion' in filters) and 'DISCUSSION_VIEW' in req.perm:
            # Create request context.
            context = Context.from_request(req)
            context.realm = 'discussion-core'

            # Get database access.
            db = self.env.get_db_cnx()
            context.cursor = db.cursor()

            # Get API component.
            api = self.env[DiscussionApi]

            # Add CSS styles and scripts.
            add_stylesheet(context.req, 'discussion/css/discussion.css')

            # Get forum events.
            for forum in api.get_changed_forums(context, start, stop):
                # Return event.
                title = 'New forum %s created' % (forum['name'],)
                description = tag(format_to_oneliner(self.env, context,
                  forum['subject']), ' - ', format_to_oneliner(self.env,
                  context, forum['description']))
                ids = ('forum', forum['id'])
                yield ('discussion unsolved', to_datetime(forum['time'], utc),
                  forum['author'], (title, description, ids))

            # Get topic events.
            for topic in api.get_changed_topics(context, start, stop):
                title = 'New topic on %s created' % (topic['forum_name'],)
                description = format_to_oneliner(self.env, context,
                  topic['subject'])
                ids = ('topic', topic['id'])
                yield ('discussion solved' if 'solved' in topic['status']
                  else 'discussion unsolved', to_datetime(topic['time'], utc),
                  topic['author'], (title, description, ids))

            # Get message events.
            for message in api.get_changed_messages(context, start, stop):
                title = 'New reply on %s created' % (message['forum_name'],)
                description = format_to_oneliner(self.env, context,
                  message['topic_subject'])
                ids = (('topic',message['topic']),'message', message['id'])
                yield ('discussion unsolved', to_datetime(message['time'], utc),
                  message['author'], (title, description, ids))

    def render_timeline_event(self, context, field, event):
        # Decompose event data.
        title, description, ids = event[3]

        # Return apropriate content.
        if field == 'url':
           url = context.href.discussion(*ids)
           if len(ids) == 3:
               url = context.href.discussion(*ids[0])
               url = '%s#%s%s' % (url,ids[1], ids[2])
           return url
        elif field == 'title':
           return tag(title)
        elif field == 'description':
           return tag(description)
