from trac.core import *
from trac.web.chrome import add_stylesheet
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.util import format_datetime, pretty_timedelta, escape, unescape, \
  Markup
from trac.util import Markup, format_datetime
import time

class DiscussionApi(object):
    def __init__(self, component, req):
        self.env = component.env
        self.log = component.log
        self.req = req
        self.db = self.env.get_db_cnx()
        self.cursor = self.db.cursor()

    # Main request processing function

    def render_discussion(self):
        # Get request mode
        group, forum, topic, message = self._get_items()
        modes = self._get_modes(group, forum, topic, message)

        # Determine moderator rights.
        if forum:
            is_moderator = (self.req.authname in forum['moderators']) or \
              self.req.perm.has_permission('DISCUSSION_ADMIN')
        else:
            is_moderator = self.req.perm.has_permission('DISCUSSION_ADMIN')

        # Perform mode actions
        self._do_action(modes, group, forum, topic, message, is_moderator)

        # Add CSS styles
        add_stylesheet(self.req, 'common/css/wiki.css')
        add_stylesheet(self.req, 'discussion/css/discussion.css')
        add_stylesheet(self.req, 'discussion/css/admin.css')

        # Fill up HDF structure and return template
        self.log.debug('modes: %s' % modes)
        self.req.hdf['discussion.authname'] = self.req.authname
        self.req.hdf['discussion.is_moderator'] = is_moderator
        self.req.hdf['discussion.group'] = group
        self.req.hdf['discussion.forum'] = forum
        self.req.hdf['discussion.topic'] = topic
        self.req.hdf['discussion.message'] = message
        self.req.hdf['discussion.mode'] = modes[-1]

        # Will be removed after template rename
        if modes[-1] == 'admin-forum-list':
            modes[-1] = 'forum-admin'
        if modes[-1] == 'admin-group-list':
            modes[-1] = 'group-admin'

        self.db.commit()
        return modes[-1] + '.cs', None

    def _get_items(self):
        group, forum, topic, message = None, None, None, None

        # Populate active group
        if self.req.args.has_key('group'):
            group_id = self.req.args.get('group')
            group = self.get_group(group_id)

        # Populate active forum
        if self.req.args.has_key('forum'):
            forum_id = self.req.args.get('forum')
            forum = self.get_forum(forum_id)

        # Populate active topic
        if self.req.args.has_key('topic'):
            topic_id = self.req.args.get('topic')
            topic = self.get_topic(topic_id)

        # Populate active topic
        if self.req.args.has_key('message'):
            message_id = self.req.args.get('message')
            message = self.get_message(message_id)

        self.log.debug('message: %s' % message)
        self.log.debug('topic: %s' % topic)
        self.log.debug('forum: %s' % forum)
        self.log.debug('group: %s' % group)
        return group, forum, topic, message

    def _get_modes(self, group, forum, topic, message):
        # Get action
        component = self.req.args.get('component')
        action = self.req.args.get('discussion_action')
        preview = self.req.args.has_key('preview');
        submit = self.req.args.has_key('submit');
        self.log.debug('component: %s' % component)
        self.log.debug('action: %s' % action)

        if component == 'admin':
            self.req.hdf['discussion.href'] = self.env.href.admin('discussion')
        elif component == 'wiki':
            self.req.hdf['discussion.href'] = self.env.href(self.req.path_info)
        else:
            self.req.hdf['discussion.href'] = self.env.href.discussion()
        self.req.hdf['discussion.component'] = component

        # Determine mode
        if message:
            if component == 'admin':
                pass
            elif component == 'wiki':
                if action == 'add':
                    return ['message-list']
                elif action == 'quote':
                    return ['message-quote', 'message-list']
                elif action == 'post-add':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-add', 'message-list']
                elif action == 'delete':
                    return ['message-delete', 'message-list']
                else:
                    return ['message-list']
            else:
                if action == 'add':
                    return ['message-list']
                elif action == 'quote':
                    return ['message-quote', 'message-list']
                elif action == 'post-add':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-add', 'message-list']
                elif action == 'delete':
                    return ['message-delete', 'message-list']
                else:
                    return ['message-list']
        if topic:
            if component == 'admin':
                pass
            elif component == 'wiki':
                if action == 'add':
                    return ['message-list']
                elif action == 'quote':
                    return ['message-quote', 'message-list']
                elif action == 'post-add':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-add', 'message-list']
                elif action == 'delete':
                    self.req.hdf['discussion.no_display'] = True
                    return ['topic-delete', 'message-list']
                else:
                    return ['message-list']
            else:
                if action == 'add':
                    return ['message-list']
                elif action == 'quote':
                    return ['message-quote', 'message-list']
                elif action == 'post-add':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-add', 'message-list']
                elif action == 'delete':
                    return ['topic-delete', 'topic-list']
                elif action == 'move':
                    return ['topic-move']
                elif action == 'post-move':
                    return ['topic-post-move', 'topic-list']
                else:
                    return ['message-list']
        elif forum:
            if component == 'admin':
                if action == 'post-edit':
                    return ['forum-post-edit', 'admin-forum-list']
                else:
                    return ['admin-forum-list']
            elif component == 'wiki':
                pass
            else:
                if action == 'add':
                    return ['topic-add']
                elif action == 'post-add':
                    if preview:
                        return ['topic-add']
                    else:
                        return ['topic-post-add', 'topic-list']
                elif action == 'delete':
                    return ['forum-delete', 'forum-list']
                else:
                    return ['topic-list']
        elif group:
            if component == 'admin':
                if action == 'post-add':
                    return ['forum-post-add', 'admin-forum-list']
                elif action == 'post-edit':
                    return ['group-post-edit', 'admin-group-list']
                elif action == 'delete':
                    return ['forums-delete', 'admin-forum-list']
                else:
                    if group['id']:
                        return ['admin-group-list']
                    else:
                        return ['admin-forum-list']
            elif component == 'wiki':
                pass
            else:
                if action == 'post-add':
                    return ['forum-post-add', 'forum-list']
                else:
                    return ['forum-list']
        else:
            if component == 'admin':
                if action == 'post-add':
                    return ['group-post-add', 'admin-group-list']
                elif action == 'delete':
                    return ['groups-delete', 'admin-group-list']
                else:
                    return ['admin-group-list']
            elif component == 'wiki':
                pass
            else:
                if action == 'add':
                    return ['forum-add']
                elif action == 'post-add':
                    return ['forum-post-add', 'forum-list']
                else:
                    return ['forum-list']

    def _do_action(self, modes, group, forum, topic, message, is_moderator):
        for mode in modes:
            if mode == 'group-list':
                self.req.perm.assert_permission('DISCUSSION_VIEW')
                self.req.hdf['discussion.groups'] = self.get_groups()
            elif mode == 'admin-group-list':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
                self.req.hdf['discussion.groups'] = self.get_groups()
            elif mode == 'group-add':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
            elif mode == 'group-post-add':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
                name = Markup(self.req.args.get('name'))
                description = Markup(self.req.args.get('description'))
                self.add_group(name, description)
            elif mode == 'group-post-edit':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
                group = self.req.args.get('group')
                name = Markup(self.req.args.get('name'))
                description = Markup(self.req.args.get('description'))
                self.edit_group(group, name, description)
            elif mode == 'group-delete':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
            elif mode == 'groups-delete':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
                selection = self.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]
                if selection:
                    for group in selection:
                        self.delete_group(group)
            elif mode == 'forum-list':
                self.req.perm.assert_permission('DISCUSSION_VIEW')
                self.req.hdf['discussion.groups'] = self.get_groups()
                self.req.hdf['discussion.forums'] = self.get_forums()
            elif mode == 'admin-forum-list':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
                self.req.hdf['discussion.users'] = self.get_users()
                self.req.hdf['discussion.groups'] = self.get_groups()
                self.req.hdf['discussion.forums'] = self.get_forums()
            elif mode == 'forum-add':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
                self.req.hdf['discussion.users'] = self.get_users()
                self.req.hdf['discussion.groups'] = self.get_groups()
            elif mode == 'forum-post-add':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
                name = Markup(self.req.args.get('name'))
                author = self.req.authname
                subject = Markup(self.req.args.get('subject'))
                description = Markup(self.req.args.get('description'))
                moderators = self.req.args.get('moderators')
                group = self.req.args.get('group')
                if not moderators:
                    moderators = []
                if not isinstance(moderators, list):
                     moderators = [moderators]
                self.add_forum(name, author, subject, description, moderators,
                  group)
            elif mode == 'forum-post-edit':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
                forum = self.req.args.get('forum')
                name = Markup(self.req.args.get('name'))
                subject = Markup(self.req.args.get('subject'))
                description = Markup(self.req.args.get('description'))
                moderators = self.req.args.get('moderators')
                group = self.req.args.get('group')
                if not moderators:
                    moderators = []
                if not isinstance(moderators, list):
                    moderators = [moderators]
                self.edit_forum(forum, name, subject, description, moderators,
                  group)
            elif mode == 'forum-delete':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
                self.delete_forum(forum['id'])
            elif mode == 'forums-delete':
                self.req.perm.assert_permission('DISCUSSION_ADMIN')
                selection = self.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]
                if selection:
                    for forum in selection:
                        self.delete_forum(forum)
            elif mode == 'topic-list':
                self.req.perm.assert_permission('DISCUSSION_VIEW')
                self.req.hdf['discussion.topics'] = self.get_topics(forum['id'])
            elif mode == 'topic-add':
                self.req.perm.assert_permission('DISCUSSION_APPEND')
                author = Markup(self.req.args.get('author'))
                body = Markup(self.req.args.get('body'))
                if author:
                    self.req.hdf['discussion.author'] = wiki_to_oneliner(author,
                      self.env)
                if body:
                    self.req.hdf['discussion.body'] = wiki_to_html(body,
                      self.env, self.req)
                self.req.hdf['discussion.time'] = format_datetime(time.time())
            elif mode == 'topic-post-add':
                self.req.perm.assert_permission('DISCUSSION_APPEND')
                subject = Markup(self.req.args.get('subject'))
                author = Markup(self.req.args.get('author'))
                body = Markup(self.req.args.get('body'))
                self.add_topic(forum['id'], subject, author, body)
            elif mode == 'topic-move':
                self.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')
                self.req.hdf['discussion.forums'] = self.get_forums()
            elif mode == 'topic-post-move':
                self.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')
                new_forum = self.req.args.get('new_forum')
                self.set_forum(topic['id'], new_forum)
            elif mode == 'topic-delete':
                self.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')
                self.delete_topic(topic['id'])
            elif mode == 'message-list':
                self.req.perm.assert_permission('DISCUSSION_VIEW')
                author = Markup(self.req.args.get('author'))
                body = Markup(self.req.args.get('body'))
                if author:
                    self.req.hdf['discussion.author'] = wiki_to_oneliner(author,
                      self.env)
                if body:
                    self.req.hdf['discussion.body'] = wiki_to_html(body,
                      self.env, self.req)
                self.req.hdf['discussion.time'] = format_datetime(time.time())
                self.req.hdf['discussion.messages'] = self.get_messages(topic['id'])
            elif mode == 'message-quote':
                self.req.perm.assert_permission('DISCUSSION_APPEND')
                lines = message['body'].splitlines()
                for I in xrange(len(lines)):
                    lines[I] = '> %s' % (lines[I])
                self.req.hdf['args.body'] = '\n'.join(lines)
            elif mode == 'message-post-add':
                self.req.perm.assert_permission('DISCUSSION_APPEND')
                author = Markup(self.req.args.get('author'))
                body = Markup(self.req.args.get('body'))
                if message:
                    self.add_message(forum['id'], topic['id'], message['id'],
                      author, body)
                else:
                    self.add_message(forum['id'], topic['id'], '-1', author, body)
            elif mode == 'message-delete':
                self.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')
                self.delete_message(message['id'])

    # Get one item functions

    def get_message(self, id):
        columns = ('id', 'forum', 'topic', 'replyto', 'time', 'author', 'body')
        sql = "SELECT id, forum, topic, replyto, time, author, body FROM" \
          " message WHERE id = %s"
        self.log.debug(sql % (id,))
        self.cursor.execute(sql, (id,))
        for row in self.cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_topic(self, id):
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
        sql = "SELECT id, forum, time, subject, body, author FROM topic WHERE" \
          " id = %s"
        self.log.debug(sql % (id,))
        self.cursor.execute(sql, (id,))
        for row in self.cursor:
            row = dict(zip(columns, row))
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            row['body'] = wiki_to_html(row['body'], self.env, self.req)
            row['time'] = format_datetime(row['time'])
            return row
        return None

    def get_topic_by_subject(self, subject):
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
        sql = "SELECT id, forum, time, subject, body, author FROM topic WHERE" \
          " subject = '%s'" % (subject)
        self.log.debug(sql)
        self.cursor.execute(sql)
        for row in self.cursor:
            row = dict(zip(columns, row))
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            row['body'] = wiki_to_html(row['body'], self.env, self.req)
            row['time'] = format_datetime(row['time'])
            return row
        return None

    def get_forum(self, id):
        columns = ('name', 'moderators', 'id', 'time', 'subject',
          'description', 'group')
        sql = "SELECT name, moderators, id, time, subject, description," \
          " forum_group FROM forum WHERE id = %s"
        self.log.debug(sql % (id,))
        self.cursor.execute(sql, (id,))
        for row in self.cursor:
            row = dict(zip(columns, row))
            row['moderators'] = row['moderators'].split(' ')
            row['description'] = wiki_to_oneliner(row['description'], self.env)
            return row
        return None

    def get_group(self, id):
        columns = ('id', 'name', 'description')
        sql = "SELECT id, name, description FROM forum_group WHERE id = %s"
        self.log.debug(sql % (id,))
        self.cursor.execute(sql, (id,))
        for row in self.cursor:
            row = dict(zip(columns, row))
            row['name'] = wiki_to_oneliner(row['name'], self.env)
            row['description'] = wiki_to_oneliner(row['description'], self.env)
            return row
        return {'id' : 0, 'name': 'None', 'description': 'No Group'}

    # Set item functions

    def set_group(self, forum, group):
        if not group:
            group = '0'
        sql = "UPDATE forum SET forum_group = %s WHERE id = %s"
        self.log.debug(sql % (group, forum))
        self.cursor.execute(sql, (group, forum))

    def set_forum(self, topic, forum):
        sql = "UPDATE topic SET forum = %s WHERE id = %s"
        self.log.debug(sql % (forum, topic))
        self.cursor.execute(sql, (forum, topic))
        sql = "UPDATE message SET forum = %s WHERE topic = %s"
        self.log.debug(sql % (forum, topic))
        self.cursor.execute(sql, (forum, topic))

    # Edit all functons

    def edit_group(self, group, name, description):
        sql = "UPDATE forum_group SET name = %s, description = %s WHERE id = %s"
        self.log.debug(sql % (name, description, group))
        self.cursor.execute(sql, (name, description, group))

    def edit_forum(self, forum, name, subject, description, moderators, group):
        moderators = ' '.join(moderators)
        if not group:
            group = '0'
        sql = "UPDATE forum SET name = %s, subject = %s, description = %s," \
          " moderators = %s, forum_group = %s WHERE id = %s"
        self.log.debug(sql % (name, subject, description, moderators,
          group, forum))
        self.cursor.execute(sql, (name, subject, description, moderators,
          group, forum))

    # Get list functions

    def get_groups(self):
        # Get count of forums without group
        sql = "SELECT COUNT(id) FROM forum WHERE forum_group = 0"
        self.log.debug(sql)
        self.cursor.execute(sql)
        no_group_forums = 0
        for row in self.cursor:
            no_group_forums = row[0]
        groups = [{'id' : 0, 'name' : 'None', 'description' : 'No Group',
          'forums' : no_group_forums}]

        # Get forum groups
        columns = ('id', 'name', 'description', 'forums')
        sql = "SELECT id, name, description, (SELECT COUNT(id) FROM forum f" \
          " WHERE f.forum_group = forum_group.id) FROM forum_group"
        self.log.debug(sql)
        self.cursor.execute(sql)
        for row in self.cursor:
            row = dict(zip(columns, row))
            row['name'] = wiki_to_oneliner(row['name'], self.env)
            row['description'] = wiki_to_oneliner(row['description'], self.env)
            groups.append(row)
        return groups

    def get_forums(self):
        columns = ('id', 'name', 'author', 'time', 'moderators', 'group',
          'subject', 'description', 'topics', 'replies', 'lastreply',
          'lasttopic')
        sql = "SELECT id, name, author, time, moderators, forum_group," \
          " subject, description, (SELECT COUNT(id) FROM topic t WHERE" \
          " t.forum = forum.id), (SELECT COUNT(id) FROM message m WHERE" \
          " m.forum = forum.id), (SELECT MAX(time) FROM message m WHERE" \
          " m.forum = forum.id), (SELECT MAX(time) FROM topic t WHERE" \
          " t.forum = forum.id) FROM forum ORDER BY subject"
        self.log.debug(sql)
        self.cursor.execute(sql)
        forums = []
        for row in self.cursor:
            row = dict(zip(columns, row))
            #row['name'] = wiki_to_oneliner(row['name'], self.env)
            #row['subject'] = wiki_to_oneliner(row['subject'], self.env)
            row['moderators'] = wiki_to_oneliner(row['moderators'], self.env)
            row['description'] = wiki_to_oneliner(row['description'], self.env)
            if row['lastreply']:
                row['lastreply'] = pretty_timedelta(row['lastreply'])
            else:
                row['lastreply'] = 'No replies'
            if row['lasttopic']:
                row['lasttopic'] = pretty_timedelta(row['lasttopic'])
            else:
                row['lasttopic'] = 'No topics'
            row['time'] = format_datetime(row['time'])
            forums.append(row)
        return forums

    def get_topics(self, forum):
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author',
          'replies', 'lastreply')
        sql = "SELECT id, forum, time, subject, body, author, (SELECT" \
          " COUNT(id) FROM message m WHERE m.topic = topic.id), (SELECT" \
          " MAX(time) FROM message m WHERE m.topic = topic.id) FROM topic" \
          " WHERE forum = %s ORDER BY time"
        self.log.debug(sql % (forum,))
        self.cursor.execute(sql, (forum,))
        topics = []
        for row in self.cursor:
            row = dict(zip(columns, row))
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            row['body'] = wiki_to_html(row['body'], self.env, self.req)
            if row['lastreply']:
                row['lastreply'] = pretty_timedelta(row['lastreply'])
            else:
                row['lastreply'] = 'No replies'
            row['time'] = format_datetime(row['time'])
            topics.append(row)
        return topics

    def get_messages(self, topic):
        columns = ('id', 'replyto', 'time', 'author', 'body')
        sql = "SELECT id, replyto, time, author, body FROM message WHERE" \
          " topic = %s ORDER BY time"
        self.log.debug(sql % (topic,))
        self.cursor.execute(sql, (topic,))

        messagemap = {}
        messages = []

        for row in self.cursor:
            row = dict(zip(columns, row))
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            row['body'] = wiki_to_html(row['body'], self.env, self.req)
            row['time'] = format_datetime(row['time'])
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
            users.append(user[0])
        return users

    # Add items functions

    def add_group(self, name, description):
        sql = "INSERT INTO forum_group (name, description) VALUES (%s, %s)"
        self.log.debug(sql % (name, description))
        self.cursor.execute(sql, (escape(name), escape(description)))


    def add_forum(self, name, author, subject, description, moderators, group):
        moderators = ' '.join(moderators)
        if not group:
            group = '0'
        sql = "INSERT INTO forum (name, author, time, moderators, subject," \
          " description, forum_group) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        self.log.debug(sql % (name, author, str(int(time.time())), moderators,
          subject, description, group))
        self.cursor.execute(sql, (escape(name), escape(author),
          str(int(time.time())), escape(moderators), escape(subject),
          escape(description), group))

    def add_topic(self, forum, subject, author, body):
        sql = "INSERT INTO topic (forum, time, author, subject, body) VALUES" \
          " (%s, %s, %s, %s, %s)"
        self.log.debug(sql % (forum, int(time.time()), author, subject, body))
        self.cursor.execute(sql, (forum, int(time.time()), escape(author),
          escape(subject), escape(body)))

    def add_message(self, forum, topic, replyto, author, body):
        sql = "INSERT INTO message (forum, topic, replyto, time, author," \
          " body) VALUES (%s, %s, %s, %s, %s, %s)"
        self.log.debug(sql % (forum, topic, replyto, int(time.time()),
          author, body))
        self.cursor.execute(sql, (forum, topic, replyto, int(time.time()),
          escape(author), escape(Markup(body))))

    # Delete items functions

    def delete_group(self, group):
        sql = "DELETE FROM forum_group WHERE id = %s"
        self.log.debug(sql % (group,))
        self.cursor.execute(sql, (group,))
        sql = "UPDATE forum SET forum_group = 0 WHERE forum_group = %s"
        self.log.debug(sql % (group,))
        self.cursor.execute(sql, (group,))

    def delete_forum(self, forum):
        sql = "DELETE FROM message WHERE forum = %s"
        self.log.debug(sql % (forum,))
        self.cursor.execute(sql, (forum,))
        sql = "DELETE FROM topic WHERE forum = %s"
        self.log.debug(sql % (forum,))
        self.cursor.execute(sql, (forum,))
        sql = "DELETE FROM forum WHERE id = %s"
        self.log.debug(sql % (forum,))
        self.cursor.execute(sql, (forum,))

    def delete_topic(self, topic):
        sql = "DELETE FROM message WHERE topic = %s"
        self.log.debug(sql % (topic,))
        self.cursor.execute(sql, (topic,))
        sql = "DELETE FROM topic WHERE id = %s"
        self.log.debug(sql % (topic,))
        self.cursor.execute(sql, (topic,))

    def delete_message(self, message):
        # Get message replies
        sql = "SELECT id FROM message WHERE replyto = %s"
        self.log.debug(sql % (message,))
        self.cursor.execute(sql, (message,))
        replies = []
        for row in self.cursor:
            replies.append(row[0])

        # Delete all replies
        for reply in replies:
            self.delete_message(reply)

        # Delete message itself
        sql = "DELETE FROM message WHERE id = %s"
        self.log.debug(sql % (message,))
        self.cursor.execute(sql, (message,))
