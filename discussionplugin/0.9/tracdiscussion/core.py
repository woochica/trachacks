from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.Timeline import ITimelineEventProvider
from trac.perm import IPermissionRequestor
from trac.util import Markup, format_datetime
import re, os, time

class DiscussionCore(Component):
    """
        The discussion module implements a message board, including wiki links to
        discussions, topics and messages.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
      IPermissionRequestor)

    # ITimelineEventProvider methods
#    def get_timeline_events(self, req, start, stop, filters):
#        if 'discussion' in filters:
#            # TODO Complete timeline magic
#            pass
#
#    def get_timeline_filters(self, req):
#        if req.perm.has_permission('DISCUSSION_VIEW'):
#            yield ('discussion', 'Discussion changes')

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['DISCUSSION_VIEW', 'DISCUSSION_MODIFY', 'DISCUSSION_MODERATE']

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('discussion', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'discussion'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('DISCUSSION_VIEW'):
            return
        yield 'mainnav', 'discussion', Markup('<a href="%s">%s</a>' % \
          (self.env.href.discussion(), self.env.config.get('discussion',
          'title', 'Discussion')))

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'''/discussion(?:/?$|/([a-zA-Z]+[-a-zA-Z]+)(?:/?$|/(\d+))(?:/?$|/(\d+)))$''',
          req.path_info)
        if match:
            forum = match.group(1)
            topic = match.group(2)
            message = match.group(3)
            if forum:
                req.args['forum'] = forum
            if topic:
                req.args['topic'] = topic
            if message:
                req.args['message'] = message
        return match

    def process_request(self, req):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'discussion/css/discussion.css')
        req.hdf['trac.href.discussion'] = self.env.href.discussion()

        forum, topic, message, mode, action, reply = None, None, None, None, \
          None, None

        # Get action
        if req.args.has_key('action'):
            action = req.args.get('action')
        if req.args.has_key('reply'):
            reply = req.args.get('reply')
        preview = req.args.has_key('preview');
        submit = req.args.has_key('submit');
        cancel = req.args.has_key('cancel');

        # Populate active forum
        if req.args.has_key('forum'):
            forum = self.get_forum(cursor, req.args.get('forum'), req)
            if not forum:
                raise TracError('No such forum %s' % req.args.get('forum'))

        # Populate active topic
        if req.args.has_key('topic'):
            topic = self.get_topic(cursor, req.args.get('topic'), req)
            if not topic:
                raise TracError('No such topic %s' % req.args.get('topic'))

        # Populate active topic
        if req.args.has_key('message'):
            message = self.get_message(cursor, req.args.get('message'), req)
            if not message:
                raise TracError('No such message %s' % req.args.get('message'))

        # Determine mode
        if topic:
            # Display list of messages
            mode = 'message-list'
        elif forum:
            if action == 'add':
                # Display add topic form?
                mode = 'topic-add'
            elif action == 'post-add':
                # Preview, cancel or post topic add?
                if preview:
                    mode = 'topic-add'
                elif cancel:
                    mode = 'topic-list'
                else:
                    mode = 'topic-post-add'
            else:
                # Display list of topics
                mode = 'topic-list'
        else:
            if action == 'add':
                # Display add forum form
                mode = 'forum-add'
            elif action == 'post-add':
                # Cancel or post forum add?
                if cancel:
                    mode = 'forum-list'
                else:
                    mode = 'forum-post-add'
            else:
                # Display list of forums
                mode = 'forum-list'

        # Forum related stuff
        if mode == 'forum-list':
            req.perm.assert_permission('DISCUSSION_VIEW')
            req.hdf['discussion.forums'] = self.get_forums(cursor, req)
        elif mode == 'forum-add':
            req.perm.assert_permission('DISCUSSION_MODIFY')
            req.hdf['discussion.users'] = self.get_users()
        elif mode == 'forum-post-add':
            req.perm.assert_permission('DISCUSSION_MODIFY')

            # Get form values
            name = req.args.get('name')
            subject = req.args.get('subject')
            description = req.args.get('description')
            moderators = req.args.get('moderators').split(' ')

            # Add new forum and display forum list
            self.add_forum(cursor, name, subject, description, moderators)
            req.hdf['discussion.forums'] = self.get_forums(cursor, req)
            mode = 'forum-list'

        # Forum topics related stuff
        elif mode == 'topic-list':
            req.perm.assert_permission('DISCUSSION_VIEW')
            req.hdf['discussion.topics'] = self.get_topics(cursor, forum['id'],
              req)
        elif mode == 'topic-add':
            req.perm.assert_permission('DISCUSSION_VIEW')

            # Get from values
            author = req.args.get('author')
            body = req.args.get('body')

            if author:
                req.hdf['discussion.author'] = wiki_to_oneliner(author, self.env)
            if body:
                req.hdf['discussion.body'] = wiki_to_html(body, self.env, req)
        elif mode == 'topic-post-add':
            req.perm.assert_permission('DISCUSSION_VIEW')

            # Get from values
            subject = req.args.get('subject')
            author = req.args.get('author')
            body = req.args.get('body')

            # Add new topic and display topic list
            self.add_topic(cursor, forum['id'], subject, author, body)
            req.hdf['discussion.topics'] = self.get_topics(cursor, forum['id'],
              req)
            mode = 'topic-list'

        # Message related stuff
        elif mode == 'message-list':
            req.perm.assert_permission('DISCUSSION_VIEW')

            # Get form values
            author = req.args.get('author')
            body = req.args.get('body')

            if action == 'post-add':
                # Submit change?
                if submit:
                    self.add_message(cursor, forum['id'], topic['id'], reply,
                      author, body)

            # Display messages
            if author:
                req.hdf['discussion.author'] = wiki_to_oneliner(author, self.env)
            if body:
                req.hdf['discussion.body'] = wiki_to_html(body, self.env, req)
            req.hdf['discussion.messages'] = self.get_messages(cursor,
              topic['id'], req)

        req.hdf['discussion.forum'] = forum
        req.hdf['discussion.topic'] = topic
        req.hdf['discussion.message'] = message
        req.hdf['discussion.mode'] = mode
        db.commit()
        return mode + '.cs', None

    # Non-extension methods
    def get_message(self, cursor, id, req):
        columns = ('id', 'forum', 'topic', 'replyto', 'time', 'author', 'body')
        cursor.execute('SELECT id, forum, topic, replyto, time, author, body,'
          'FROM message WHERE id=%s', [id])
        for row in cursor:
            row = dict(zip(columns, row))
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            row['body'] = wiki_to_html(row['body'], self.env, req)
            return row
        return None

    def get_topic(self, cursor, id, req):
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
        cursor.execute('SELECT id, forum, time, subject, body, author FROM'
          ' topic WHERE id=%s', [id])
        for row in cursor:
            row = dict(zip(columns, row))
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            row['body'] = wiki_to_html(row['body'], self.env, req)
            return row
        return None

    def get_forum(self, cursor, id, req):
        columns = ('name', 'moderators', 'id', 'time', 'subject', 'description')
        cursor.execute('SELECT name, moderators, id, time, subject, description'
          ' FROM forum WHERE name=%s', [id])
        for row in cursor:
            row = dict(zip(columns, row))
            row['moderators'] = row['moderators'].split(' ')
            row['description'] = wiki_to_oneliner(row['description'], self.env)
            return row
        return None

    def get_forums(self, cursor, req):
        columns = ('moderators', 'id', 'time', 'subject', 'name',
          'description', 'topics', 'replies')
        cursor.execute('SELECT moderators, id, time, subject, name,'
          ' description, (SELECT COUNT(id) FROM topic t WHERE'
          ' t.forum = forum.id), (SELECT COUNT(id) FROM message m WHERE m.forum'
          ' = forum.id) FROM forum ORDER BY subject')
        forums = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['moderators'] = wiki_to_oneliner(row['moderators'], self.env)
            row['description'] = wiki_to_oneliner(row['description'], self.env)
            row['time'] = format_datetime(row['time'])
            forums.append(row)
        return forums

    def get_topics(self, cursor, forum, req):
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author', 'replies')
        cursor.execute('SELECT id, forum, time, subject, body, author, (SELECT'
          ' COUNT(id) FROM message m WHERE m.topic = topic.id) FROM topic'
          ' WHERE forum = %s ORDER BY time', [forum])
        topics = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            row['body'] = wiki_to_html(row['body'], self.env, req)
            row['time'] = format_datetime(row['time'])
            topics.append(row)
        return topics

    def get_messages(self, cursor, topic, req):
        columns = ('id', 'replyto', 'time', 'author', 'body')
        cursor.execute('SELECT id, replyto, time, author, body FROM message'
          ' WHERE topic = "%s" ORDER BY time' % (topic))

        messagemap = {}
        messages = []

        for row in cursor:
            row = dict(zip(columns, row))
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            row['body'] = wiki_to_html(row['body'], self.env, req)
            messagemap[row['id']] = row
            # Add top-level messages to the main list, in order of time
            if row['replyto'] == -1:
                messages.append(row)

        # Second pass, add replies
        for message in messagemap.values():
            if message['replyto'] != -1:
                parent = messagemap[message['replyto']]
                if 'replies' in parent:
                    parent['replies'].append(message)
                else:
                    parent['replies'] = [message]
        return messages;

    def get_users(self):
        users = []
        for user in self.env.get_known_users():
            users.append(user)
        return users

    def add_forum(self, cursor, name, subject, description, moderators):
        moderators = ' '.join(moderators)
        cursor.execute('INSERT INTO forum (name, time, moderators, subject,'
          ' description) VALUES ("%s", "%s", "%s", "%s", "%s")' % (name,
          str(int(time.time())), moderators, subject, description))

    def add_topic(self, cursor, forum, subject, author, body):
        cursor.execute('INSERT INTO topic (forum, time, author, subject,'
          ' body) VALUES ("%s", "%s", "%s", "%s", "%s")' % (forum,
          str(int(time.time())), author, subject, body))

    def add_message(self, cursor, forum, topic, replyto, author, body):
         cursor.execute('INSERT INTO message (forum, topic, replyto, time,'
          ' author, body) VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' % (
            forum, topic, replyto, str(int(time.time())), author, body))
