from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.Timeline import ITimelineEventProvider
from trac.perm import IPermissionRequestor
import re, os

class DiscussionCore(Component):
    """
        The discussion module implements a message board, including wiki links to
        discussions, topics and messages.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, IPermissionRequestor)

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
    def get_htdocs_dir(self):
        return os.path.join(self.env.config.get('discussion', 'path'), 'htdocs')

    def get_templates_dir(self):
        return os.path.join(self.env.config.get('discussion', 'path'), 'templates')

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'discussion'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('DISCUSSION_VIEW'):
            return
        yield 'mainnav', 'discussion', '<a href="%s">%s</a>' % (self.env.href.discussion(), self.env.config.get('discussion', 'title', 'Discussion'))

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'''/discussion(?:/?$|/([a-z]+[-a-z]+)(?:/?$|/(\d+))(?:/?$|/(\d+)))$''', req.path_info)
        if match:
            req.args['forum'] = match.group(1) or ''
            req.args['topic'] = match.group(2) or ''
            req.args['message'] = match.group(3) or ''
        return match

    def process_request(self, req):
        req.perm.assert_permission('DISCUSSION_VIEW')
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        add_stylesheet(req, 'css/wiki.css')
        add_stylesheet(req, 'css/discussion.css')
        req.hdf['trac.href.discussion'] = self.env.href.discussion()

        forum, topic, message = None, None, None
        mode = 'forum-list'

        # Populate active forum
        if req.args['forum']:
            forum = self.get_forum(cursor, req.args['forum'], req)
            if not forum: raise TracError('No such forum %s' % req.args['forum'])
            req.hdf['discussion.forum'] = forum
            mode = 'topic-list'

        # Populate active topic
        if req.args['topic']:
            topic = self.get_topic(cursor, req.args['topic'], req)
            if not topic: raise TracError('No such topic %s' % req.args['topic'])
            req.hdf['discussion.topic'] = topic
            mode = 'message-list'

        # Populate active topic
        if req.args['message']:
            message = self.get_message(cursor, req.args['message'], req)
            if not message: raise TracError('No such message %s' % req.args['message'])
            req.hdf['discussion.message'] = message
            mode = 'message-list'

        req.hdf['discussion.mode'] = mode

        # Do we have some actions?
        if 'action' in req.args:
            req.hdf['debug'] = req.args['action']

        # Do mode specific stuff
        if mode == 'forum-list':
            req.hdf['discussion.forums'] = self.get_forums(cursor, req)
        elif mode == 'topic-list':
            req.hdf['discussion.topics'] = self.get_topics(cursor, forum['id'], req)
        elif mode == 'message-list':
            req.hdf['discussion.messages'] = self.get_messages(cursor, topic['id'], req)

        return mode + '.cs', None

    # Non-extension methods
    def get_message(self, cursor, id, req):
        columns = ('id', 'forum', 'topic', 'replyto', 'time', 'body', 'author')
        cursor.execute('SELECT %s FROM message WHERE id=%s' % (', '.join(columns), id))
        row = cursor.fetchone()
        if not row: return None
        row = dict(zip(columns, row))
        row['body'] = wiki_to_html(row['body'], self.env, req)
        return row

    def get_topic(self, cursor, id, req):
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
        cursor.execute('SELECT %s FROM topic WHERE id=%s' % (', '.join(columns), id))
        row = cursor.fetchone()
        if not row: return None
        row = dict(zip(columns, row))
        row['subject'] = wiki_to_oneliner(row['subject'], self.env)
        return row

    def get_forum(self, cursor, id, req):
        columns = ('name', 'moderators', 'id', 'time', 'subject', 'description')
        cursor.execute('SELECT %s FROM forum WHERE name=\'%s\'' % (', '.join(columns), id))
        row = cursor.fetchone()
        if not row: return None
        row = dict(zip(columns, row))
        row['moderators'] = row['moderators'].split(' ')
        row['subject'] = wiki_to_oneliner(row['subject'], self.env)
        return row

    def get_forums(self, cursor, req):
        columns = ('moderators', 'id', 'time', 'subject', 'name', 'description', 'topics', 'replies')
        cursor.execute('SELECT moderators, id, time, subject, name, description, (SELECT COUNT(id) FROM topic t WHERE t.forum=forum.id), (SELECT COUNT(id) FROM message m WHERE m.forum = forum.id) FROM forum ORDER BY subject')
        forums = []
        for row in cursor.fetchall():
            row = dict(zip(columns, row))
            row['moderators'] = row['moderators'].split(' ')
            row['subject'] = wiki_to_oneliner(row['subject'], self.env)
            forums.append(row)
        return forums

    def get_topics(self, cursor, forum, req):
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author', 'replies')
        cursor.execute('SELECT id, forum, time, subject, body, author, (SELECT COUNT(id) FROM message m WHERE m.topic = topic.id) FROM topic WHERE forum = %s ORDER BY time' % forum)
        topics = []
        for row in cursor.fetchall():
            row = dict(zip(columns, row))
            row['subject'] = wiki_to_oneliner(row['subject'], self.env)
            topics.append(row)
        return topics

    def get_messages(self, cursor, topic, req):
        columns = ('id', 'replyto', 'time', 'body', 'author')
        cursor.execute('SELECT %s FROM message WHERE topic=%s ORDER BY time' % (', '.join(columns), topic))

        messagemap = {}
        messages = []

        for message in cursor.fetchall():
            message = dict(zip(columns, message))
            message['body'] = wiki_to_html(message['body'], self.env, req)
            messagemap[message['id']] = message
            # Add top-level messages to the main list, in order of time
            if not message['replyto']:
                messages.append(message)

        # Second pass, add replies
        for message in messagemap.values():
            if message['replyto']:
                parent = messagemap[message['replyto']]
                if 'replies' in parent:
                    parent['replies'].append(message)
                else:
                    parent['replies'] = [ message ]
        return messages;
