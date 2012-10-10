# -*- coding: utf-8 -*-

# Standard imports.
import time, re

# Genshi imports.
from genshi.builder import tag

# Trac imports.
from trac.core import *
from trac.wiki.web_ui import WikiModule
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.web.href import Href
from trac.web.chrome import Chrome, add_stylesheet
from trac.util import format_date, format_datetime
from trac.util.text import to_unicode
from trac.util.translation import _

# Trac interfaces.
from trac.web.main import IRequestFilter
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider

# Local imports.
from tracdiscussion.api import *
from tracdiscussion.core import *

class DiscussionWiki(Component):
    """
        The wiki module implements macros for forums, topics and messages
        referencing.
    """
    implements(IWikiSyntaxProvider, IWikiMacroProvider, IRequestFilter)

    # Wiki macro documentations.

    view_topic_doc = _("Displays content of a discussion topic. If no argument "
      "passed tries to find the topic with the same name as is the name of the "
      "current wiki page. If the topic name is passed, displays that topic. ")

    recent_topics_doc = _("Lists all topics that have been recently active "
      "grouping them by the day they were lastly active. This macro accepts "
      "two parameters. The first is a forum ID. If provided, only topics in "
      "that forum are included in the resulting list. If omitted, topics from "
      "all forums are listed. The second parameter is a number for limiting "
      "the number of topics returned. For example, specifying a limit of 5 "
      "will result in only the five most recently active topics to be included "
      "in the list.")

    # IWikiSyntaxProvider methods

    def get_link_resolvers(self):
        yield ('forum', self._discussion_link)
        yield ('last-forum', self._discussion_link)
        yield ('topic', self._discussion_link)
        yield ('last-topic', self._discussion_link)
        yield ('message', self._discussion_link)
        yield ('topic-attachment', self._discussion_attachment_link)
        yield ('raw-topic-attachment', self._discussion_attachment_link)

    def get_wiki_syntax(self):
        return []

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'ViewTopic'
        yield 'RecentTopics'

    def get_macro_description(self, name):
        if name == 'ViewTopic':
            return self.view_topic_doc
        elif name == 'RecentTopics':
            return self.recent_topics_doc
        else:
            return ""

    def expand_macro(self, formatter, name, content):
        if name == 'ViewTopic':
            return self._expand_view_topic(formatter, name, content)
        elif name == 'RecentTopics':
            return self._expand_recent_topics(formatter, name, content)
        else:
            raise TracError('Not implemented macro %s' % (name))

    # IRequestFilter methods.

    def pre_process_request(self, req, handler):
        # Change method from POST to GET.
        match = re.match(r'^/wiki(?:/(.*))?', req.path_info)
        action = req.args.get('discussion_action')
        if match and action and req.method == 'POST':
            req.environ['REQUEST_METHOD'] = 'GET'

        # Continue processing request.
        return handler

    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)

    # Internal methods.

    def _expand_view_topic(self, formatter, name, content):
        self.log.debug("Rendering ViewTopic macro...")

        # Check permission
        if not formatter.perm.has_permission('DISCUSSION_VIEW'):
            return

        # Determine topic subject
        page_name = formatter.req.path_info[6:] or 'WikiStart'
        subject = content or page_name

        # Create request context.
        context = Context.from_request(formatter.req)
        context.realm = 'discussion-wiki'

        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Get API component.
        api = self.env[DiscussionApi]

        # Get topic by subject
        try:
            id = int(subject)
            topic = api.get_topic(context, id)
        except:
            topic = api.get_topic_by_subject(context, subject)
        self.log.debug('subject: %s' % (subject,))
        self.log.debug('topic: %s' % (topic,))

        # Prepare request and resource object.
        if topic:
            context.req.args['topic'] = topic['id']
            context.resource = Resource('discussion', 'topic/%s' % (topic['id']
              ,))

        # Process discussion request.
        template, data = api.process_discussion(context)

        # Return rendered template.
        data['discussion']['mode'] = 'message-list'
        data['discussion']['page_name'] = page_name
        if context.redirect_url:
            # Generate HTML elements for redirection.
            href = context.req.href(context.redirect_url[0]) + \
              context.redirect_url[1]
            self.log.debug("Redirecting to %s" % (href))
            return tag.div(tag.strong('Redirect: '),
              ' This page redirects to ', tag.a(href, href = href),
              tag.script("window.location = '" + context.req.href('discussion',
              'redirect', redirect_url = href) + "'", language = "JavaScript"),
              class_ = "system-message")
        else:
            # Render template.
            return to_unicode(Chrome(self.env).render_template(formatter.req,
              template, data, 'text/html', True))

    def _expand_recent_topics(self, formatter, name, content):
        self.log.debug("Rendering RecentTopics macro...")

        # Check permission
        if not formatter.perm.has_permission('DISCUSSION_VIEW'):
            return

        # Create request context.
        context = Context.from_request(formatter.req)
        context.realm = 'discussion-wiki'

        # Check if TracTags plugin is enabled.
        context.has_tags = is_tags_enabled(self.env)

        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Get API object.
        api = self.env[DiscussionApi]

        # Get list of Trac users.
        context.users = api.get_users(context)

        # Parse macro arguments.
        arguments = []
        forum_id = None
        limit = 10
        if content:
            arguments = [argument.strip() for argument in content.split(',')]
        if len(arguments) == 1:
            limit = arguments[0]
        elif len(arguments) == 2:
            forum_id = arguments[0]
            limit = arguments[1]
        else:
            raise TracError("Invalid number of macro arguments.")

        # Construct and execute SQL query.
        columns = ('forum', 'topic', 'time')
        values = []
        if forum_id:
            values.append(forum_id)
        if limit:
            values.append(limit)
        values = tuple(values)
        sql = ("SELECT forum, topic, MAX(time) as max_time "
               "FROM "
               "  (SELECT forum, topic, time "
               "  FROM message "
               "  UNION "
               "  SELECT forum, id as topic, time "
               "  FROM topic)" +
               (forum_id and " WHERE forum = %s" or "") +
               "  GROUP BY topic "
               "  ORDER BY max_time DESC" +
               (limit and " LIMIT %s" or ""))
        self.log.debug(sql % values)
        context.cursor.execute(sql, values)

        # Collect recent topics.
        entries = []
        for row in context.cursor:
            row = dict(zip(columns, row))
            entries.append(row)

        self.log.debug(entries)

        # Format entries data.
        entries_per_date = []
        prevdate = None
        for entry in entries:
            date = format_date(entry['time'])
            if date != prevdate:
                prevdate = date
                entries_per_date.append((date, []))
            forum_name = api.get_forum(context, entry['forum'])['name']
            topic_subject = api.get_topic_subject(context, entry['topic'])
            entries_per_date[-1][1].append((entry['forum'], forum_name,
              entry['topic'], topic_subject))

        # Format result.
        return tag.div((tag.h3(date), tag.ul(tag.li(tag.a(forum_name, href =
          formatter.href.discussion('forum', forum_id)), ': ', tag.a(
          topic_subject, href = formatter.href.discussion('topic', topic_id)))
          for forum_id, forum_name, topic_id, topic_subject in entries)) for
          date, entries in entries_per_date)

    def _discussion_link(self, formatter, namespace, params, label):
        try:
           id = int(params)
        except:
           id = -1

        # Create request context.
        context = Context.from_request(formatter.req)
        context.realm = 'discussion-wiki'

        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        if namespace == 'forum':
            columns = ('subject',)
            sql = ("SELECT f.subject "
                   "FROM forum f "
                   "WHERE f.id = %s")
            values = (id,)
            self.log.debug(sql % values)
            context.cursor.execute(sql, values)
            for row in context.cursor:
                row = dict(zip(columns, row))
                return tag.a(label, href = formatter.href.discussion('forum',
                  id), title = row['subject'].replace('"', ''))
            return tag.a(label, href = formatter.href.discussion('forum', id),
              title = label, class_ = 'missing')
        elif namespace == 'last-forum':
            columns = ('id', 'subject')
            sql = ("SELECT f.id, f.subject "
                   "FROM forum f "
                   "WHERE f.time = "
                   "  (SELECT MAX(time) "
                   "  FROM forum "
                   "  WHERE forum_group = %s)")
            values = (id,)
            self.log.debug(sql % values)
            context.cursor.execute(sql, values)
            for row in context.cursor:
                row = dict(zip(columns, row))
                return tag.a(label, href = formatter.href.discussion('forum',
                  row['id']), title = row['subject'].replace('"', ''))
            return tag.a(label, href = formatter.href.discussion('forum',
              '-1'), title = label, class_ = 'missing')
        elif namespace == 'topic':
            columns = ('forum', 'forum_subject', 'subject')
            sql = ("SELECT t.forum, f.subject, t.subject "
                   "FROM topic t "
                   "LEFT JOIN forum f "
                   "ON t.forum = f.id "
                   "WHERE t.id = %s")
            values = (id,)
            self.log.debug(sql % values)
            context.cursor.execute(sql, values)
            for row in context.cursor:
                row = dict(zip(columns, row))
                return tag.a(label, href = '%s#-1' % \
                  (formatter.href.discussion('topic', id),), title =
                  ('%s: %s' % (row['forum_subject'], row['subject']))
                  .replace('"', ''))
            return tag.a(label, href = formatter.href.discussion('topic', id),
              title = label.replace('"', ''), class_ = 'missing')
        elif namespace == 'last-topic':
            columns = ('id', 'forum_subject', 'subject')
            sql = ("SELECT t.id, f.subject, t.subject "
                   "FROM topic t "
                   "LEFT JOIN forum f "
                   "ON t.forum = f.id WHERE t.time = "
                   "  (SELECT MAX(time) "
                   "  FROM topic "
                   "  WHERE forum = %s)")
            values = (id,)
            self.log.debug(sql % values)
            context.cursor.execute(sql, values)
            for row in context.cursor:
                row = dict(zip(columns, row))
                return tag.a(label, href = '%s#-1' % \
                  (formatter.href.discussion('topic', row['id']),), title =
                  ('%s: %s' % (row['forum_subject'], row['subject']))
                  .replace('"', ''))
            return tag.a(label, href = formatter.href.discussion('topic',
              '-1'), title = label.replace('"', ''), class_ = 'missing')
        elif namespace == 'message':
            columns = ('forum', 'topic', 'forum_subject', 'subject')
            sql = ("SELECT m.forum, m.topic, f.subject, t.subject "
              "FROM message m, "
                "(SELECT subject, id "
                "FROM forum) f, "
                "(SELECT subject, id "
                "FROM topic) t "
              "WHERE m.forum = f.id AND m.topic = t.id AND m.id = %s")
            values = (id,)
            self.log.debug(sql % values)
            context.cursor.execute(sql, values)
            for row in context.cursor:
                row = dict(zip(columns, row))
                return tag.a(label, href = '%s#%s' % \
                  (formatter.href.discussion('message', id), id), title = (
                  '%s: %s' % (row['forum_subject'], row['subject'])).replace(
                  '"', ''))
            return tag.a(label, href = formatter.href.discussion('message', id),
              title = label.replace('"', ''), class_ = 'missing')
        else:
            return tag.a(label, href = formatter.href.discussion('message', id),
              title = label.replace('"', ''), class_ = 'missing')

    def _discussion_attachment_link(self, formatter, namespace, params, label):
        id, name = params.split(':')

        # Create request context.
        context = Context.from_request(formatter.req)
        context.realm = 'discussion-wiki'

        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        if namespace == 'topic-attachment':
            return format_to_html(self.env, context,
              '[attachment:discussion:topic/%s:%s %s]' % (id, name, label))
        elif namespace == 'raw-topic-attachment':
            return format_to_html(self.env, context,
              '[raw-attachment:discussion:topic/%s:%s %s]' % (id, name, label))
        else:
            return tag.a(label, href = formatter.href.discussion('topic', id),
              title = label.replace('"', ''), class_ = 'missing')
