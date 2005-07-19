from trac.core import *
from trac.wiki import IWikiSyntaxProvider

class DiscussionWiki(Component):
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
        if ns != 'forum':
            try:
                id = int(params)
            except ValueError:
                return '<div class="system-message"><strong>Error:</strong> Invalid %s id "%s"</div>\n' % (ns, params)
        else:
            id = params
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if ns == 'forum':
            cursor.execute('SELECT subject FROM forum WHERE name=%s', id)
            row = cursor.fetchone()
            if row:
                subject = row[0]
                return '<a href="%s/%s" title="%s">%s</a>' % (self.env.href.discussion(), id, subject, label)
            else:
                return '<a href="%s/%s" class="missing">%s?</a>' % (self.env.href.discussion(), id, label)
        elif ns == 'topic':
            cursor.execute('SELECT (SELECT name FROM forum WHERE id=topic.forum), (SELECT subject FROM forum WHERE id=topic.forum), subject FROM topic WHERE id=%i', id)
            row = cursor.fetchone()
            if row:
                forum, forum_subject, subject = row
                return '<a href="%s/%s/%s" title="%s: %s">%s</a>' % (self.env.href.discussion(), forum, id, forum_subject, subject, label)
        elif ns == 'message':
            cursor.execute('SELECT (SELECT name FROM forum WHERE id=message.forum), topic, (SELECT subject FROM forum WHERE id=message.forum), (SELECT subject FROM topic WHERE id=message.topic) FROM message WHERE id=%i', id)
            row = cursor.fetchone()
            if row:
                forum, topic, forum_subject, subject = row
                return '<a href="%s/%s/%s/%s" title="%s: %s">%s</a>' % (self.env.href.discussion(), forum, topic, id, forum_subject, subject, label)
        return '<a href="%s" class="missing">%s?</a>' % (self.env.href.discussion(), label)
