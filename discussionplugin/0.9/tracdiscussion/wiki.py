from trac.core import *
from trac.wiki import IWikiSyntaxProvider

class DiscussionWiki(Component):
    """
        The wiki module implements macros for forums, topics and messages
        referencing.
    """
    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider
    def get_link_resolvers(self):
        yield ('forum', self._discussion_link)
        yield ('topic', self._discussion_link)
        yield ('message', self._discussion_link)

    def get_wiki_syntax(self):
        return []

    # Core code
    def _discussion_link(self, formatter, ns, params, label):
        id = params

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if ns == 'forum':
            columns = ('subject',)
            sql = 'SELECT subject FROM forum WHERE id = %s' % (id)
            self.log.debug(sql)
            cursor.execute(sql)
            for row in cursor:
                row = dict(zip(columns, row))
                return '<a href="%s/%s" title="%s">%s</a>' % (
                  self.env.href.discussion(), id, row['subject'], label)
            return '<a href="%s/%s" class="missing">%s?</a>' % (
              self.env.href.discussion(), id, label)
        elif ns == 'topic':
            columns = ('forum', 'forum_subject', 'subject')
            sql = 'SELECT forum, (SELECT subject FROM forum WHERE id =' \
              ' topic.forum), subject FROM topic WHERE id = %s' % (id)
            self.log.debug(sql)
            cursor.execute(sql)
            for row in cursor:
                row = dict(zip(columns, row))
                forum, forum_subject, subject = row
                return '<a href="%s/%s/%s#-1" title="%s: %s">%s</a>' % (
                  self.env.href.discussion(), row['forum'], id,
                  row['forum_subject'], row['subject'], label)
            return '<a href="%s/%s" class="missing">%s?</a>' % (
              self.env.href.discussion(), id, label)
        elif ns == 'message':
            columns = ('forum', 'topic', 'forum_subject', 'subject')
            sql = 'SELECT forum, topic, (SELECT subject FROM forum WHERE id =' \
              ' message.forum), (SELECT subject FROM topic WHERE id =' \
              ' message.topic) FROM message WHERE id = %s' % (id)
            self.log.debug(sql)
            cursor.execute(sql)
            for row in cursor:
                row = dict(zip(columns, row))
                return '<a href="%s/%s/%s/%s#%s" title="%s: %s">%s</a>' % (
                  self.env.href.discussion(), row['forum'], row['topic'], id,
                    id, row['forum_subject'], row['subject'], label)
            return '<a href="%s/%s" class="missing">%s?</a>' % (
              self.env.href.discussion(), id, label)
        return '<a href="%s" class="missing">%s?</a>' % (
          self.env.href.discussion(), label)
