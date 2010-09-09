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
            # Create context.
            context = Context.from_request(req)
            context.realm = 'discussion-core'

            # Get database access.
            db = self.env.get_db_cnx()
            context.cursor = db.cursor()

            # Add CSS styles and scripts.
            add_stylesheet(context.req, 'discussion/css/discussion.css')

            # Get forum events
            for forum in self._get_changed_forums(context, start, stop):
                # Return event.
                title = 'New forum %s created' % (forum['name'],)
                description = tag(forum['subject'], ' - ', forum['description'])
                ids = ('forum', forum['id'])
                yield ('discussion', forum['time'], forum['author'], (title,
                  description, ids))

            # Get topic events
            for topic in self._get_changed_topics(context, start, stop):
                title = 'New topic on %s created' % (topic['forum_name'])
                description = topic['subject']
                ids = ('topic', topic['id'])
                yield ('discussion', topic['time'], topic['author'], (title,
                  description, ids))

            # Get message events
            for message in self._get_changed_messages(context, start, stop):
                title = 'New reply on %s created' % (message['forum_name'])
                description = message['topic_subject']
                ids = ('message', message['id'])
                yield ('discussion', message['time'], message['author'], (title,
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
        sql_values = {'start' : to_timestamp(start),
          'stop' : to_timestamp(stop)}
        sql = ("SELECT f.id, f.name, f.author, f.subject, f.description, f.time "
               "FROM forum f "
               "WHERE f.time BETWEEN %(start)s AND %(stop)s" % (sql_values))
        self.log.debug(sql)
        context.cursor.execute(sql)
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
        sql_values = {'start' : to_timestamp(start),
          'stop' : to_timestamp(stop)}
        sql = ("SELECT t.id, t.subject, t.body, t.author, t.time, t.forum, "
                 "f.name "
               "FROM topic t "
               "LEFT JOIN "
                 "(SELECT id, name "
                 "FROM forum) f "
               "ON t.forum = f.id "
               "WHERE t.time BETWEEN %(start)s AND %(stop)s" % (sql_values))
        self.log.debug(sql)
        context.cursor.execute(sql)
        for row in context.cursor:
            row = dict(zip(columns, row))
            row['time'] = to_datetime(row['time'], utc)
            row['subject'] = format_to_oneliner(self.env, context,
              row['subject'])
            yield row

    def _get_changed_messages(self, context, start, stop):
        columns = ('id', 'author', 'time', 'forum', 'topic', 'body', 'forum_name',
          'topic_subject')
        sql_values = {'start' : to_timestamp(start),
          'stop' : to_timestamp(stop)}
        sql = ("SELECT m.id, m.author, m.time, m.forum, m.topic, m.body, "
                 "f.name, t.subject "
               "FROM message m, "
                 "(SELECT id, name "
                 "FROM forum) f, "
                 "(SELECT id, subject "
                 "FROM topic) t "
               "WHERE t.id = m.topic AND f.id = m.forum AND time BETWEEN "
               "%(start)s AND %(stop)s" % (sql_values))
        self.log.debug(sql)
        context.cursor.execute(sql)
        for row in context.cursor:
            row = dict(zip(columns, row))
            row['time'] = to_datetime(row['time'], utc)
            row['topic_subject'] = format_to_oneliner(self.env, context,
              row['topic_subject'])
            yield row
