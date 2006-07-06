from tracdiscussion.api import *
from trac.core import *
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider
from trac.web.chrome import add_stylesheet
from trac.util import format_datetime
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
            # Get access to database
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            # Add CSS stylesheet
            add_stylesheet(req, 'discussion/css/discussion.css')

            # Get form values
            action = req.args.get('discussion_action')
            author = req.args.get('author')
            body = req.args.get('body')
            reply = req.args.get('reply')
            preview = req.args.has_key('preview');
            submit = req.args.has_key('submit');
            cancel = req.args.has_key('cancel');

            # Determine mode
            if action == 'add':
                mode = 'message-list'
            if action == 'post-add':
                if submit:
                    mode = 'message-post-add'
                else:
                    mode = 'message-list'
            elif action == 'delete':
                if reply == '-1':
                    mode = 'topic-delete'
                else:
                    mode = 'message-delete'
            else:
                mode = 'message-list'

            # Determine topic name to display
            if content:
                subject = content
            else:
                subject = req.path_info[6:] or 'WikiStart'

            # Get topic and forum
            topic = get_topic_by_subject(cursor, self.env, req, self.log, subject)
            if not topic:
                 req.hdf['discussion.href'] = self.env.href(req.path_info)
                 req.hdf['discussion.topic_name'] = subject
                 return "<h2>Discussion</h2><span>No discussion for this page created.</span>"
            forum = get_forum(cursor, self.env, req, self.log, topic['forum'])

            # Determine moderator rights.
            is_moderator = (req.authname in forum['moderators']) or \
              req.perm.has_permission('DISCUSSION_MODIFY')

            # Perform selected mode action
            if mode == 'message-list':
                req.perm.assert_permission('DISCUSSION_VIEW')
            elif mode == 'message-post-add':
                req.perm.assert_permission('DISCUSSION_VIEW')

                # Add new message
                add_message(cursor, self.log, forum['id'], topic['id'], reply,
                  author, body)
            elif mode == 'message-delete':
                req.perm.assert_permission('DISCUSSION_MODERATE')

                # Check if user can moderate
                if not is_moderator:
                   raise PermissionError('Forum moderate')

                # Delete message
                delete_message(cursor, self.log, reply)
            elif mode == 'topic-delete':
                req.perm.assert_permission('DISCUSSION_MODERATE')

                # Check if user can moderate
                if not is_moderator:
                   raise PermissionError('Forum moderate')

                # Delete topic
                delete_topic(cursor, self.log, topic['id'])
                return "<h2>Discussion</h2><span>No discussion for this page created.</span>"

            # Set template values and return rendered macro
            db.commit()
            req.hdf['discussion.href'] = self.env.href(req.path_info)
            if req.authname:
                req.hdf['discussion.authname'] = req.authname
            if author:
                req.hdf['discussion.author'] = wiki_to_oneliner(author, self.env)
            if body:
                req.hdf['discussion.body'] = wiki_to_html(body, self.env, req)
            req.hdf['discussion.time'] = format_datetime(time.time())
            req.hdf['discussion.is_moderator'] = is_moderator
            req.hdf['discussion.topic'] = topic
            req.hdf['discussion.messages'] = get_messages(cursor, self.env,
              req, self.log, topic['id'])
            req.hdf['discussion.no_navigation'] = True
            return req.hdf.render('message-list.cs')
        else:
            raise TracError('Not implemented macro %s' % (name))

    # Core code
    def _discussion_link(self, formatter, ns, params, label):
        id = params

        self.log.debug(ns)

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if ns == 'forum':
            columns = ('subject',)
            sql = "SELECT subject FROM forum WHERE id = %s"
            self.log.debug(sql)
            cursor.execute(sql, (id,))
            for row in cursor:
                row = dict(zip(columns, row))
                return '<a href="%s/%s" title="%s">%s</a>' % (
                  self.env.href.discussion(), id, row['subject'], label)
            return '<a href="%s/%s" class="missing">%s?</a>' % (
              self.env.href.discussion(), id, label)
        elif ns == 'topic':
            columns = ('forum', 'forum_subject', 'subject')
            sql = "SELECT forum, (SELECT subject FROM forum WHERE id =" \
              " topic.forum), subject FROM topic WHERE id = %s"
            self.log.debug(sql)
            cursor.execute(sql, (id,))
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
            sql = "SELECT forum, topic, (SELECT subject FROM forum WHERE id =" \
              " message.forum), (SELECT subject FROM topic WHERE id =" \
              " message.topic) FROM message WHERE id = %s"
            self.log.debug(sql)
            cursor.execute(sql, (id,))
            for row in cursor:
                row = dict(zip(columns, row))
                return '<a href="%s/%s/%s/%s#%s" title="%s: %s">%s</a>' % (
                  self.env.href.discussion(), row['forum'], row['topic'], id,
                    id, row['forum_subject'], row['subject'], label)
            return '<a href="%s/%s" class="missing">%s?</a>' % (
              self.env.href.discussion(), id, label)
        else:
          return '<a href="%s" class="missing">%s?</a>' % (
            self.env.href.discussion(), label)
