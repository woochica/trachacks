from tracdiscussion.api import *
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor, PermissionError
from trac.util import Markup, format_datetime
import re, os, time

class DiscussionCore(Component):
    """
        The core module implements a message board, including wiki links to
        discussions, topics and messages.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
      IPermissionRequestor)

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
        if req.perm.has_permission('DISCUSSION_VIEW'):
            yield 'mainnav', 'discussion', Markup('<a href="%s">%s</a>' % \
              (self.env.href.discussion(), self.env.config.get('discussion',
              'title', 'Discussion')))

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'''/discussion(?:/?$|/(\d+)(?:/?$|/(\d+))(?:/?$|/(\d+)))$''',
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
        # Get access to database
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # CSS styles
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'discussion/css/discussion.css')

        forum, topic, message, mode, is_moderator = None, None, None, None, False

        # Get action
        action = req.args.get('discussion_action')
        reply = req.args.get('reply')
        preview = req.args.has_key('preview');
        submit = req.args.has_key('submit');
        cancel = req.args.has_key('cancel');

        # Populate active forum
        if req.args.has_key('forum'):
            forum = get_forum(cursor, self.env, req, self.log,
              req.args.get('forum'))
            if not forum:
                raise TracError('No such forum %s' % req.args.get('forum'))

            # Determine moderator rights.
            is_moderator = (req.authname in forum['moderators']) or \
              req.perm.has_permission('DISCUSSION_MODIFY')

        # Populate active topic
        if req.args.has_key('topic'):
            topic = get_topic(cursor, self.env, req, self.log,
              req.args.get('topic'))
            if not topic:
                raise TracError('No such topic %s' % req.args.get('topic'))

        # Populate active topic
        if req.args.has_key('message'):
            message = get_message(cursor, self.env, req, self.log,
              req.args.get('message'))
            if not message:
                raise TracError('No such message %s' % req.args.get('message'))

        # Determine mode
        if topic:
            # Display list of messages
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
            elif action == 'move':
                mode = 'topic-move'
            elif action == 'post-move':
                if submit:
                    mode = 'topic-post-move'
                else:
                    mode = 'message-list'
            else:
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
            elif action == 'delete':
                mode = 'forum-delete'
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
            req.hdf['discussion.href'] = self.env.href.discussion()
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
            req.hdf['discussion.forums'] = get_forums(cursor, self.env, req,
              self.log)
        elif mode == 'forum-add':
            req.perm.assert_permission('DISCUSSION_MODIFY')
            req.hdf['discussion.href'] = self.env.href.discussion()
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
            req.hdf['discussion.users'] = get_users(self.env, self.log)
        elif mode == 'forum-post-add':
            req.perm.assert_permission('DISCUSSION_MODIFY')

            # Get form values
            name = req.args.get('name')
            author = req.authname
            subject = req.args.get('subject')
            description = req.args.get('description')
            moderators = req.args.get('moderators')
            group = req.args.get('group')
            if not moderators:
                moderators = []
            if not isinstance(moderators, list):
                moderators = [moderators]

            # Add new forum
            add_forum(cursor, self.log, name, author, subject, description,
              moderators, group)

            # Display forum list
            req.hdf['discussion.href'] = self.env.href.discussion()
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
            req.hdf['discussion.forums'] = get_forums(cursor, self.env, req,
              self.log)
            mode = 'forum-list'
        elif mode == 'forum-delete':
            req.perm.assert_permission('DISCUSSION_MODIFY')

            # Delete current forum
            delete_forum(cursor, self.log, forum['id'])

            # Display forum list
            req.hdf['discussion.href'] = self.env.href.discussion()
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
            req.hdf['discussion.forums'] = get_forums(cursor, self.env, req,
              self.log)
            mode = 'forum-list'

        # Forum topics related stuff
        elif mode == 'topic-list':
            req.perm.assert_permission('DISCUSSION_VIEW')
            req.hdf['discussion.href'] = self.env.href.discussion(forum['id'])
            req.hdf['discussion.topics'] = get_topics(cursor, self.env, req,
              self.log, forum['id'])
        elif mode == 'topic-add':
            req.perm.assert_permission('DISCUSSION_VIEW')

            if req.authname:
                req.hdf['discussion.authname'] = req.authname

            # Get form values
            author = req.args.get('author')
            body = req.args.get('body')

            req.hdf['discussion.href'] = self.env.href.discussion(forum['id'])
            if author:
                req.hdf['discussion.author'] = wiki_to_oneliner(author, self.env)
            if body:
                req.hdf['discussion.body'] = wiki_to_html(body, self.env, req)
            req.hdf['discussion.time'] = format_datetime(time.time())
        elif mode == 'topic-post-add':
            req.perm.assert_permission('DISCUSSION_VIEW')

            # Get from values
            subject = req.args.get('subject')
            author = req.args.get('author')
            body = req.args.get('body')

            # Add new topic and display topic list
            add_topic(cursor, self.log, forum['id'], subject, author, body)
            req.hdf['discussion.href'] = self.env.href.discussion(forum['id'])
            req.hdf['discussion.topics'] = get_topics(cursor, self.env, req,
              self.log, forum['id'])
            mode = 'topic-list'
        elif mode == 'topic-move':
            req.perm.assert_permission('DISCUSSION_MODERATE')

            # Check if user can moderate
            if not is_moderator:
                raise PermissionError('Forum moderate')

            # Display change forum form
            req.hdf['discussion.href'] = self.env.href.discussion(forum['id'], topic['id'])
            req.hdf['discussion.forums'] = get_forums(cursor, self.env, req, self.log)
        elif mode == 'topic-post-move':
            req.perm.assert_permission('DISCUSSION_MODERATE')

            # Check if user can moderate
            if not is_moderator:
                raise PermissionError('Forum moderate')

            # Get form values
            new_forum = req.args.get('new_forum')

            # Set new forum
            set_forum(cursor, self.log, topic['id'], new_forum)

            # Display topics
            req.hdf['discussion.href'] = self.env.href.discussion(forum['id'])
            req.hdf['discussion.topics'] = get_topics(cursor, self.env, req,
              self.log, forum['id'])
            mode = 'topic-list'
        elif mode == 'topic-delete':
            req.perm.assert_permission('DISCUSSION_MODERATE')

            # Check if user can moderate
            if not is_moderator:
                raise PermissionError('Forum moderate')

            # Delete topic
            delete_topic(cursor, self.log, topic['id'])

            # Display topics
            req.hdf['discussion.href'] = self.env.href.discussion(forum['id'])
            req.hdf['discussion.topics'] = get_topics(cursor, self.env, req,
              self.log, forum['id'])
            mode = 'topic-list'

        # Message related stuff
        elif mode == 'message-list':
            req.perm.assert_permission('DISCUSSION_VIEW')

            if req.authname:
                req.hdf['discussion.authname'] = req.authname

            # Get form values
            author = req.args.get('author')
            body = req.args.get('body')

            # Display messages
            req.hdf['discussion.href'] = self.env.href.discussion(forum['id'],
              topic['id'])
            if author:
                req.hdf['discussion.author'] = wiki_to_oneliner(author, self.env)
            if body:
                req.hdf['discussion.body'] = wiki_to_html(body, self.env, req)
            req.hdf['discussion.time'] = format_datetime(time.time())
            req.hdf['discussion.messages'] = get_messages(cursor, self.env, req,
              self.log, topic['id'])
        elif mode == 'message-post-add':
            req.perm.assert_permission('DISCUSSION_VIEW')

            # Get form values
            author = req.args.get('author')
            body = req.args.get('body')

            # Add new message
            add_message(cursor, self.log, forum['id'], topic['id'], reply,
              author, body)

            # Display messages
            req.hdf['discussion.href'] = self.env.href.discussion(forum['id'],
              topic['id'])
            if author:
                req.hdf['discussion.author'] = wiki_to_oneliner(author, self.env)
            if body:
                req.hdf['discussion.body'] = wiki_to_html(body, self.env, req)
            req.hdf['discussion.messages'] = get_messages(cursor, self.env, req,
              self.log, topic['id'])
            mode = 'message-list'
        elif mode == 'message-delete':
            req.perm.assert_permission('DISCUSSION_MODERATE')

            # Check if user can moderate
            if not is_moderator:
                raise PermissionError('Forum moderate')

            # Delete message
            delete_message(cursor, self.log, reply)

            # Display or messages
            req.hdf['discussion.href'] = self.env.href.discussion(forum['id'],
              topic['id'])
            req.hdf['discussion.messages'] = get_messages(cursor, self.env, req,
              self.log, topic['id'])
            mode = 'message-list'

        req.hdf['trac.href.discussion'] = self.env.href.discussion()
        req.hdf['discussion.forum'] = forum
        req.hdf['discussion.topic'] = topic
        req.hdf['discussion.message'] = message
        req.hdf['discussion.mode'] = mode
        req.hdf['discussion.is_moderator'] = is_moderator
        db.commit()
        return mode + '.cs', None
