# -*- coding: utf8 -*-

from tracdiscussion.api import *
from tracdiscussion.core import *
from trac.core import *
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider
from trac.web.main import IRequestHandler, IRequestFilter
from trac.web.chrome import add_stylesheet
from trac.util import format_datetime
from trac.util.html import html
import time, re

view_topic_doc = """Displays content of discussion topic. If no argument passed
tries to find topic with same name as name of current wiki page. If topic name
passed displays that topic. """

class DiscussionWiki(Component):
    """
        The wiki module implements macros for forums, topics and messages
        referencing.
    """
    implements(IWikiSyntaxProvider, IWikiMacroProvider, IRequestFilter)

    # IWikiSyntaxProvider methods
    def get_link_resolvers(self):
        yield ('forum', self._discussion_link)
        yield ('topic', self._discussion_link)
        yield ('message', self._discussion_link)

    def get_wiki_syntax(self):
        return []

    # IWikiMacroProvider methods
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

            # Return macro content
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

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        match = re.match(r'^/wiki(?:/(.*))?', req.path_info)
        action = req.args.get('discussion_action')
        redirect = req.args.get('redirect', '0')
        if match and action in ('post-add', 'post-edit', 'delete') \
          and redirect == '1':
            return self
        else:
            return handler

    def post_process_request(self, req, template, content_type):
        return (template, content_type)

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'^/wiki(?:/(.*))?', req.path_info)
        return match

    def process_request(self, req):
        # Determine topic subject
        subject = req.path_info[6:] or 'WikiStart'

        # Get database access
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Get topic by subject
        api = DiscussionApi(self, req)
        topic = api.get_topic_by_subject(cursor, subject)
        self.log.debug('topic: %s' % (topic,))

        # Return macro content
        if topic:
            req.hdf['discussion.no_navigation'] = True
            req.args['component'] = 'wiki'
            req.args['forum'] = str(topic['forum'])
            req.args['topic'] = str(topic['id'])
            template, type = api.render_discussion(req, cursor)
            db.commit()

        # Redirect to wiki page
        req.args['redirect'] = '0'
        req.redirect(req.href.wiki(**dict(req.args.items())))

    # Core code methods
    def _discussion_link(self, formatter, ns, params, label):
        id = params

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if ns == 'forum':
            columns = ('subject',)
            sql = "SELECT f.subject FROM forum f WHERE f.id = %s"
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
            sql = "SELECT t.forum, (SELECT f.subject FROM forum f, topic t" \
              " WHERE f.id = t.forum), t.subject FROM topic t WHERE t.id = %s"
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
            sql = "SELECT m.forum, m.topic, (SELECT f.subject FROM forum f," \
              " message m WHERE f.id = m.forum), (SELECT t.subject FROM" \
              " topic t, message m WHERE t.id = m.topic) FROM message m" \
              " WHERE m.id = %s"
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
