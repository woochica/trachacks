# -*- coding: utf-8 -*-

from trac.core import *
from trac.mimeview import Context
from trac.config import Option
from trac.search import ISearchSource, shorten_result, search_to_sql
from trac.util import shorten_line
from trac.util.datefmt import to_datetime, utc

class DiscussionSearch(Component):
    """
        The search module implements searching in topics and messages.
    """
    implements(ISearchSource)

    title = Option('discussion', 'title', 'Discussion',
      'Main navigation bar button title.')

    # ISearchSource methods.

    def get_search_filters(self, req):
        if 'DISCUSSION_VIEW' in req.perm:
            yield ('discussion', self.title)

    def get_search_results(self, req, terms, filters):
        if not 'discussion' in filters:
            return

        # Create context.
        context = Context.from_request(req)
        context.realm = 'discussion-core'

        # Get database access.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Search in topics.
        query, args = search_to_sql(db, ['author', 'subject', 'body'], terms)
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
        sql = "SELECT id, forum, time, subject, body, author FROM topic" \
          " WHERE " + query
        self.log.debug(sql)
        cursor.execute(sql, args)
        for row in cursor:
            row = dict(zip(columns, row))
            row['time'] = to_datetime(row['time'], utc)
            yield (req.href.discussion('topic', row['id']) + '#-1',
              "Topic #%d: %s" % (row['id'], shorten_line(row['subject'])),
              row['time'], row['author'], shorten_result(row['body'], [query]))

        # Search in messages
        query, args = search_to_sql(db, ['m.author', 'm.body',
          't.subject'],  terms)
        columns = ('id', 'forum', 'topic', 'time', 'author', 'body', 'subject')
        sql = "SELECT m.id, m.forum, m.topic, m.time, m.author, m.body," \
          " t.subject FROM message m LEFT JOIN (SELECT subject, id FROM" \
          " topic) t ON t.id = m.topic WHERE " + query
        self.log.debug(sql)
        cursor.execute(sql, args)
        for row in cursor:
            row = dict(zip(columns, row))
            row['time'] = to_datetime(row['time'], utc)
            yield (req.href.discussion('message', row['id']) + '#%s' % (
              row['id']), "Message  #%d: %s" % (row['id'], shorten_line(
              row['subject'])), row['time'], row['author'], shorten_result(
              row['body'], [query]))
