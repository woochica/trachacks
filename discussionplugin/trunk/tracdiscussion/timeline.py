# -*- coding: utf8 -*-

from genshi.builder import tag

from trac.core import *
from trac.mimeview import Context
from trac.config import Option
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util.datefmt import to_timestamp, to_datetime, utc
from trac.util.text import to_unicode

from trac.timeline import ITimelineEventProvider

class DiscussionTimeline(Component):
    """
        The timeline module implements raising timeline events when
        forums, topics and messages are changed.
    """
    implements(ITimelineEventProvider)

    title = Option('discussion', 'title', 'Discussion',
      'Main navigation bar button title.')

    # ITimelineEventProvider
    def get_timeline_filters(self, req):
        if 'DISCUSSION_VIEW' in req.perm:
            yield ('discussion', self.title + ' changes')

    def get_timeline_events(self, req, start, stop, filters):
        self.log.debug("start: %s, stop: %s, filters: %s" % (start, stop,
          filters))
        if ('discussion' in filters) and 'DISCUSSION_VIEW' in req.perm:
            # Create context.
            context = Context.from_request(req)('discussion')

            # Get database access.
            db = self.env.get_db_cnx()
            context.cursor = db.cursor()

            # Get forum events
            for forum in self._get_changed_forums(context, start, stop):
                # Return event.
                title = 'New forum %s created' % (forum['name'],)
                description = tag(forum['subject'], ' - ', forum['description'])
                ids = (forum['id'],)
                yield ('changeset', forum['time'], forum['author'], (title,
                  description, ids))

            # Get topic events
            for topic in self._get_changed_topics(context, start, stop):
                title = 'New topic on %s created' % (topic['forum_name'])
                description = topic['subject']
                ids = (topic['forum'], topic['id'])
                yield ('newticket', topic['time'], topic['author'], (title,
                  description, ids))

            # Get message events
            for message in self._get_changed_messages(context, start, stop):
                title = 'New reply on %s created' % (message['forum_name'])
                description = message['topic_subject']
                ids = (message['forum'], message['topic'], message['id'])
                yield ('newticket', message['time'], message['author'], (title,
                  description, ids))

    def render_timeline_event(self, context, field, event):
        # Decompose event data.
        title, description, ids = event[3]

        # Return apropriate content.
        if field == 'url':
           url = context.href.discussion(*ids)
           if len(ids) == 3:
               url = '%s#%s' % (url, ids[2])
           return url
        elif field == 'title':
           return tag(title)
        elif field == 'description':
           return tag(description)

    # Internal methods.
    def _get_changed_forums(self, context, start, stop):
        columns = ('id', 'name', 'author', 'subject', 'description', 'time')
        sql = "SELECT f.id, f.name, f.author, f.subject, f.description," \
          " f.time FROM forum f WHERE f.time BETWEEN %s AND %s"
        self.log.debug(sql % (start, stop))
        context.cursor.execute(sql, (to_timestamp(start), to_timestamp(stop)))
        for row in context.cursor:
            row = dict(zip(columns, row))
            row['time'] = to_datetime(row['time'], utc)
            row['subject'] = format_to_oneliner(self.env, context,
              row['subject'])
            row['description'] = format_to_oneliner(self.env, context,
              row['description'])
            yield row

    def _get_changed_topics(self, context, start, stop):
        columns = ('id', 'subject', 'body', 'author', 'time', 'forum',
          'forum_name')
        sql = "SELECT t.id, t.subject, t.body, t.author, t.time, t.forum," \
          " f.name FROM topic t LEFT JOIN (SELECT id, name FROM forum)" \
          " f ON t.forum = f.id WHERE t.time BETWEEN %s AND %s"
        self.log.debug(sql % (start, stop))
        context.cursor.execute(sql, (to_timestamp(start), to_timestamp(stop)))
        for row in context.cursor:
            row = dict(zip(columns, row))
            row['time'] = to_datetime(row['time'], utc)
            row['subject'] = format_to_oneliner(self.env, context,
              row['subject'])
            yield row

    def _get_changed_messages(self, context, start, stop):
        columns = ('id', 'author', 'time', 'forum', 'topic', 'body', 'forum_name',
          'topic_subject')
        sql = "SELECT m.id, m.author, m.time, m.forum, m.topic, m.body, f.name," \
          " t.subject FROM message m, (SELECT id, name FROM forum) f, (SELECT" \
          " id, subject FROM topic) t WHERE t.id = m.topic AND f.id = m.forum" \
          " AND time BETWEEN %s AND %s"
        self.log.debug(sql % (start, stop))
        context.cursor.execute(sql, (to_timestamp(start), to_timestamp(stop)))
        for row in context.cursor:
            row = dict(zip(columns, row))
            row['time'] = to_datetime(row['time'], utc)
            row['topic_subject'] = format_to_oneliner(self.env, context,
              row['topic_subject'])
            yield row
