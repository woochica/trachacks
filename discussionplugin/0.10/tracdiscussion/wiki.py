from tracdiscussion.api import *
from tracdiscussion.core import *
from trac.core import *
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider
from trac.web.chrome import add_stylesheet
from trac.util import format_datetime
from trac.util.html import html
import time

view_topic_doc = """Displays content of discussion topic. If no argument passed
tries to find topic with same name as name of current wiki page. If topic name
passed displays that topic. """

class DiscussionWiki(Component):
    """
        The wiki module implements macros for forums, topics and messages
        referencing.
    """
    implements(IWikiSyntaxProvider, IWikiMacroProvider)

    # IWikiSyntaxProvider
    def get_link_resolvers(self):
        yield ('forum', self._discussion_link)
        yield ('topic', self._discussion_link)
        yield ('message', self._discussion_link)

    def get_wiki_syntax(self):
        return []

    # IWikiMacroProvider
    def get_macros(self):
        yield 'ViewTopic'

    def get_macro_description(self, name):
        if name == 'VisitCounter':
            return view_topic_doc
        else:
            return ""

    def render_macro(self, req, name, content):
        if name == 'ViewTopic':
            # Determine topic subject
            if content:
                subject = content
            else:
                subject = req.path_info[6:] or 'WikiStart'

            # Get database access
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            # Get topic by subject
            api = DiscussionApi(self, req)
            topic = api.get_topic_by_subject(cursor, subject)
            self.log.debug('topic: %s' % (topic,))

            # Retrun macro content
            if topic:
                req.hdf['discussion.no_navigation'] = True
                req.args['component'] = 'wiki'
                req.args['forum'] = str(topic['forum'])
                req.args['topic'] = str(topic['id'])
                template, type = api.render_discussion(req, cursor)
                db.commit()
                return req.hdf.render(template)
            else:
                req.hdf['discussion.no_navigation'] = True
                return req.hdf.render('message-list.cs')
        else:
            raise TracError('Not implemented macro %s' % (name))

    # Core code
    def _discussion_link(self, formatter, ns, params, label):
        id = params

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if ns == 'forum':
            columns = ('subject',)
            sql = "SELECT subject FROM forum WHERE id = %s"
            self.log.debug(sql % (id,))
            cursor.execute(sql, (id,))
            for row in cursor:
                row = dict(zip(columns, row))
                return html.a(label, href = formatter.href.discussion(id),
                  title = row['subject'])
            return html.a(label, href = '%s/%s' % (formatter.href.discussion(),
              id), title = label, class_ = 'missing')
        elif ns == 'topic':
            columns = ('forum', 'forum_subject', 'subject')
            sql = "SELECT forum, (SELECT subject FROM forum WHERE id =" \
              " topic.forum), subject FROM topic WHERE id = %s"
            self.log.debug(sql % (id,))
            cursor.execute(sql, (id,))
            for row in cursor:
                row = dict(zip(columns, row))
                return html.a(label, href = '%s#-1' % \
                  (formatter.href.discussion(row['forum'], id),), title =
                  '%s: %s' % (row['forum_subject'], row['subject']))
            return html.a(label, href = '%s/%s' % (formatter.href.discussion(),
              id), title = label, class_ = 'missing')
        elif ns == 'message':
            columns = ('forum', 'topic', 'forum_subject', 'subject')
            sql = "SELECT forum, topic, (SELECT subject FROM forum WHERE id =" \
              " message.forum), (SELECT subject FROM topic WHERE id =" \
              " message.topic) FROM message WHERE id = %s"
            self.log.debug(sql % (id,))
            cursor.execute(sql, (id,))
            for row in cursor:
                row = dict(zip(columns, row))
                return html.a(label, href = '%s#%s' % \
                  (formatter.href.discussion(row['forum'], row['topic'], id),
                  id), title = '%s: %s' % (row['forum_subject'],
                  row['subject']))
            return html.a(label, href = '%s/%s' % (formatter.href.discussion(),
              id), title = label, class_ = 'missing')
        else:
            return html.a(label, href = '%s/%s' % (formatter.href.discussion(),
              id), title = label, class_ = 'missing')
