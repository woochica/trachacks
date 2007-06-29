# -*- coding: utf8 -*-

from trac.core import *
from trac.context import Context
from trac.config import Option
from trac.timeline import ITimelineEventProvider, TimelineEvent
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util.datefmt import to_timestamp, to_datetime, utc

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
            context = Context(self.env, req)('discussion')
            context.cursor = context.db.cursor()

            # Determine timeline format.
            format = req.args.get('format')
            self.log.debug("format: %s" % (format))

            # Get forum events
            for forum in self._get_changed_forums(context, start, stop):
                # Prepare event object attributes.
                event = TimelineEvent(self, 'changeset')
                event.set_changeinfo(forum['time'], forum['author'],
                  forum['author'] != 'anonymous')
                event.add_markup(title = 'New forum %s' % (forum['name']),
                  header = forum['subject'] + ' - ')
                event.add_wiki(context, body = forum['description'])
                event.href_fragment = unicode(forum['id'])

                # Return event.
                yield event

            # Get topic events
            for topic in self._get_changed_topics(context, start, stop):
                # Prepare event object attributes.
                event = TimelineEvent(self, 'newticket')
                event.set_changeinfo(topic['time'], topic['author'],
                  topic['author'] != 'anonymous')
                event.add_markup(title = 'New topic on %s' %
                  (topic['forum_name']), header = topic['subject'] + ' - ')
                event.add_wiki(context, body = topic['body'])
                event.href_fragment = '%s/%s' % (topic['forum'], topic['id'])

                # Return event.
                yield event

            # Get message events
            for message in self._get_changed_messages(context, start, stop):
                # Prepare event object attributes.
                event = TimelineEvent(self, 'editedticket')
                event.set_changeinfo(message['time'], message['author'],
                  message['author'] != 'anonymous')
                event.add_markup(title = 'New reply on %s' %
                  (message['forum_name']), header = message['topic_subject'] +
                  ' - ')
                event.add_wiki(context, body = message['body'])
                event.href_fragment = '%s/%s/%s#%s' % (message['forum'],
                  message['topic'], message['id'], message['id'])

                # Return event.
                yield event

    def event_formatter(self, event, wikitext_key):
        return None

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
            row['subject'] = format_to_oneliner(context, row['subject'])
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
            row['topic_subject'] = format_to_oneliner(context, row['topic_subject'])
            yield row
