# -*- coding: utf-8 -*-

from trac.core import *
from trac.Search import ISearchSource, shorten_result
from trac import util

class DiscussionSearch(Component):
    """
        The search module implements searching in topics and messages.
    """
    implements(ISearchSource)

    #�ISearchSource
    def get_search_filters(self, req):
        if req.perm.has_permission('DISCUSSION_VIEW'):
            yield ("discussion", "Discussion")

    def get_search_results(self, req, query, filters):
        if not 'discussion' in filters:
            return

        # Create database context
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Search in topics.
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
        sql = "SELECT id, forum, time, subject, body, author FROM topic" \
          " WHERE subject || body LIKE '%%%s%%'" % (query)
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            yield (self.env.href.discussion(row['forum'], row['id']) + '#-1',
              "topic: %d: %s" % (row['id'], util.shorten_line(row['subject'])),
              row['time'], row['author'], shorten_result(row['body'],
              query.split()))

        # Search in messages
        columns = ('id', 'forum', 'topic', 'time', 'author', 'body', 'subject')
        sql = "SELECT id, forum, topic, time, author, body, (SELECT" \
          " subject FROM topic t WHERE t.id = message.topic) FROM message" \
          " WHERE body LIKE '%%%s%%'" % (query)
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            yield (self.env.href.discussion(row['forum'], row['topic'],
              row['id']) + '#%s' % (row['id']), "message: %d: %s" %
              (row['id'], util.shorten_line(row['subject'])), row['time'],
              row['author'], shorten_result(row['body'], query.split()))
