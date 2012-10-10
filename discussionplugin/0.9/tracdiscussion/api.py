# -*- coding: utf-8 -*-

from trac.core import *
from trac.web.chrome import add_stylesheet
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.perm import PermissionError
from trac.util import format_datetime, pretty_timedelta, escape, unescape, \
  Markup
import time

class DiscussionApi(object):
    def __init__(self, component, req):
        self.env = component.env
        self.log = component.log

    # Main request processing function

    def render_discussion(self, req, cursor):
        # Get request mode
        group, forum, topic, message = self._get_items(req, cursor)
        modes = self._get_modes(req, group, forum, topic, message)
        self.log.debug('modes: %s' % modes)

        # Determine moderator rights.
        if forum:
            is_moderator = (req.authname in forum['moderators']) or \
              req.perm.has_permission('DISCUSSION_ADMIN')
        else:
            is_moderator = req.perm.has_permission('DISCUSSION_ADMIN')

        # Perform mode actions
        self._do_action(req, cursor, modes, group, forum, topic, message,
          is_moderator)

        # Add CSS styles
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'discussion/css/discussion.css')
        add_stylesheet(req, 'discussion/css/admin.css')

        # Fill up HDF structure and return template
        req.hdf['discussion.authname'] = req.authname
        req.hdf['discussion.is_moderator'] = is_moderator
        if group:
            group['name'] = wiki_to_oneliner(group['name'], self.env)
            group['description'] = wiki_to_oneliner(group['description'],
              self.env)
            req.hdf['discussion.group'] = group
        if forum:
            forum['name'] = wiki_to_oneliner(forum['name'], self.env)
            forum['description'] = wiki_to_oneliner(forum['description'],
              self.env)
            forum['subject'] = wiki_to_oneliner(forum['subject'], self.env)
            forum['time'] = format_datetime(forum['time'])
            req.hdf['discussion.forum'] = forum
        if topic:
            topic['subject'] = wiki_to_oneliner(topic['subject'], self.env)
            topic['author'] = wiki_to_oneliner(topic['author'], self.env)
            topic['body'] = wiki_to_html(topic['body'], self.env, req)
            topic['time'] = format_datetime(topic['time'])
            req.hdf['discussion.topic'] = topic
        if message:
            message['author'] = wiki_to_oneliner(message['author'], self.env)
            message['body'] = wiki_to_html(message['body'], self.env, req)
            message['time'] = format_datetime(message['time'])
            req.hdf['discussion.message'] = message
        req.hdf['discussion.mode'] = modes[-1]
        req.hdf['discussion.time'] = format_datetime(time.time())
        return modes[-1] + '.cs', None

    def _get_items(self, req, cursor):
        group, forum, topic, message = None, None, None, None

        # Populate active group
        if req.args.has_key('group'):
            group_id = req.args.get('group')
            group = self.get_group(cursor, group_id)

        # Populate active forum
        if req.args.has_key('forum'):
            forum_id = req.args.get('forum')
            forum = self.get_forum(cursor, forum_id)

        # Populate active topic
        if req.args.has_key('topic'):
            topic_id = req.args.get('topic')
            topic = self.get_topic(cursor, topic_id)

        # Populate active topic
        if req.args.has_key('message'):
            message_id = req.args.get('message')
            message = self.get_message(cursor, message_id)

        self.log.debug('message: %s' % message)
        self.log.debug('topic: %s' % topic)
        self.log.debug('forum: %s' % forum)
        self.log.debug('group: %s' % group)
        return group, forum, topic, message

    def _get_modes(self, req, group, forum, topic, message):
        # Get action
        component = req.args.get('component')
        action = req.args.get('discussion_action')
        preview = req.args.has_key('preview');
        submit = req.args.has_key('submit');
        self.log.debug('component: %s' % component)
        self.log.debug('action: %s' % action)

        if component == 'admin':
            req.hdf['discussion.href'] = self.env.href.admin('discussion')
        elif component == 'wiki':
            req.hdf['discussion.href'] = self.env.href(req.path_info)
        else:
            req.hdf['discussion.href'] = self.env.href.discussion()
        req.hdf['discussion.component'] = component

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
                elif action == 'edit':
                    return ['message-edit', 'message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-edit', 'message-list']
                elif action == 'delete':
                    return ['message-delete', 'message-list']
                elif action == 'set-display':
                    return ['message-set-display', 'message-list']
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
                elif action == 'edit':
                    return ['message-edit', 'message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-edit', 'message-list']
                elif action == 'delete':
                    return ['message-delete', 'message-list']
                elif action == 'set-display':
                    return ['message-set-display', 'message-list']
                else:
                    return ['message-list']
        if topic:
            if component == 'admin':
                pass
            elif component == 'wiki':
                if action == 'add':
                    return ['message-list']
                elif action == 'quote':
                    return ['topic-quote', 'message-list']
                elif action == 'post-add':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-add', 'message-list']
                elif action == 'edit':
                    return ['topic-edit', 'message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['message-list']
                    else:
                        return ['topic-post-edit', 'message-list']
                elif action == 'delete':
                    req.hdf['discussion.no_display'] = True
                    return ['topic-delete', 'message-list']
                elif action == 'set-display':
                    return ['message-set-display', 'message-list']
                else:
                    return ['message-list']
            else:
                if action == 'add':
                    return ['message-list']
                elif action == 'quote':
                    return ['topic-quote', 'message-list']
                elif action == 'post-add':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-add', 'message-list']
                elif action == 'edit':
                    return ['topic-edit', 'message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['message-list']
                    else:
                        return ['topic-post-edit', 'message-list']
                elif action == 'delete':
                    return ['topic-delete', 'topic-list']
                elif action == 'move':
                    return ['topic-move']
                elif action == 'post-move':
                    return ['topic-post-move', 'topic-list']
                elif action == 'set-display':
                    return ['message-set-display', 'message-list']
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

    def _do_action(self, req, cursor, modes, group, forum, topic, message,
      is_moderator):
        for mode in modes:
            self.log.debug('doing %s mode action' % (mode,))
            if mode == 'group-list':
                req.perm.assert_permission('DISCUSSION_VIEW')

                # Display groups.
                req.hdf['discussion.groups'] = self.get_groups(req, cursor)

            elif mode == 'admin-group-list':
                req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values
                order = req.args.get('order') or 'id'
                desc = req.args.get('desc')

                # Prepare ORDER BY statement
                order_by = 'ORDER BY ' + order
                if desc:
                    order_by = order_by + ' DESC'
                else:
                    order_by = order_by + ' ASC'

                # Display groups.
                req.hdf['discussion.order'] = order
                req.hdf['discussion.desc'] = desc
                if group:
                    req.hdf['discussion.name'] = group['name']
                    req.hdf['discussion.description'] = \
                      group['description']
                req.hdf['discussion.groups'] = self.get_groups(req, cursor, order_by)

            elif mode == 'group-add':
                req.perm.assert_permission('DISCUSSION_ADMIN')

            elif mode == 'group-post-add':
                req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                new_name = Markup(req.args.get('name'))
                new_description = Markup(req.args.get('description'))

                # Add new group.
                self.add_group(cursor, new_name, new_description)

            elif mode == 'group-post-edit':
                req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                new_group = req.args.get('group')
                new_name = Markup(req.args.get('name'))
                new_description = Markup(req.args.get('description'))

                # Edit group.
                self.edit_group(cursor, new_group, new_name, new_description)

            elif mode == 'group-delete':
                req.perm.assert_permission('DISCUSSION_ADMIN')

            elif mode == 'groups-delete':
                req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get selected groups.
                selection = req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete selected groups.
                if selection:
                    for group_id in selection:
                        self.delete_group(cursor, group_id)

            elif mode == 'forum-list':
                req.perm.assert_permission('DISCUSSION_VIEW')

                # Get form values
                order = req.args.get('order') or 'id'
                desc = req.args.get('desc')

                # Prepare ORDER BY statement
                order_by = 'ORDER BY ' + order
                if desc:
                    order_by = order_by + ' DESC'
                else:
                    order_by = order_by + ' ASC'

                # Display forums.
                req.hdf['discussion.order'] = order
                req.hdf['discussion.desc'] = desc
                req.hdf['discussion.groups'] = self.get_groups(req, cursor)
                req.hdf['discussion.forums'] = self.get_forums(req, cursor,
                  order_by)

            elif mode == 'admin-forum-list':
                req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values
                order = req.args.get('order') or 'id'
                desc = req.args.get('desc')

                # Prepare ORDER BY statement
                order_by = 'ORDER BY ' + order
                if desc:
                    order_by = order_by + ' DESC'
                else:
                    order_by = order_by + ' ASC'

                # Display forums.
                req.hdf['discussion.order'] = order
                req.hdf['discussion.desc'] = desc
                self.log.debug(forum)
                if forum:
                    req.hdf['discussion.name'] = forum['name']
                    req.hdf['discussion.subject'] = forum['subject']
                    req.hdf['discussion.description'] = \
                      forum['description']
                    req.hdf['discussion.moderators'] = forum['moderators']
                    req.hdf['discussion.group'] = forum['group']
                req.hdf['discussion.users'] = self.get_users()
                req.hdf['discussion.groups'] = self.get_groups(req, cursor)
                req.hdf['discussion.forums'] = self.get_forums(req, cursor, order_by)

            elif mode == 'forum-add':
                req.perm.assert_permission('DISCUSSION_ADMIN')

                # Display Add Forum form.
                req.hdf['discussion.users'] = self.get_users()
                req.hdf['discussion.groups'] = self.get_groups(req, cursor)

            elif mode == 'forum-post-add':
                req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values
                new_name = Markup(req.args.get('name'))
                new_author = req.authname
                new_subject = Markup(req.args.get('subject'))
                new_description = Markup(req.args.get('description'))
                new_moderators = req.args.get('moderators')
                new_group = req.args.get('group')
                if not new_moderators:
                    new_moderators = []
                if not isinstance(new_moderators, list):
                     new_moderators = [new_moderators]

                # Perform new forum add.
                self.add_forum(cursor, new_name, new_author, new_subject,
                   new_description, new_moderators, new_group)

            elif mode == 'forum-post-edit':
                req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                new_forum = req.args.get('forum')
                new_name = Markup(req.args.get('name'))
                new_subject = Markup(req.args.get('subject'))
                new_description = Markup(req.args.get('description'))
                new_moderators = req.args.get('moderators')
                new_group = req.args.get('group')
                if not new_moderators:
                    new_moderators = []
                if not isinstance(new_moderators, list):
                    new_moderators = [new_moderators]

                # Perform forum edit.
                self.edit_forum(cursor, new_forum, new_name, new_subject,
                  new_description, new_moderators, new_group)

            elif mode == 'forum-delete':
                req.perm.assert_permission('DISCUSSION_ADMIN')

                # Delete forum
                self.delete_forum(cursor, forum['id'])

            elif mode == 'forums-delete':
                req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get selected forums.
                selection = req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete selected forums.
                if selection:
                    for forum_id in selection:
                        self.delete_forum(cursor, forum_id)

            elif mode == 'topic-list':
                req.perm.assert_permission('DISCUSSION_VIEW')

                # Get form values
                order = req.args.get('order') or 'id'
                desc = req.args.get('desc')

                # Prepare ORDER BY statement
                order_by = 'ORDER BY ' + order
                if desc:
                    order_by = order_by + ' DESC'
                else:
                    order_by = order_by + ' ASC'

                # Display topics.
                req.hdf['discussion.order'] = order
                req.hdf['discussion.desc'] = desc
                req.hdf['discussion.topics'] = self.get_topics(req, cursor,
                  forum['id'], order_by)

            elif mode == 'topic-add':
                req.perm.assert_permission('DISCUSSION_APPEND')

                # Get form values.
                new_subject = Markup(req.args.get('subject'))
                new_author = Markup(req.args.get('author'))
                new_body = Markup(req.args.get('body'))

                # Display Add Topic form.
                if new_subject:
                    req.hdf['discussion.subject'] = wiki_to_oneliner(
                      new_subject, self.env)
                if new_author:
                    req.hdf['discussion.author'] = wiki_to_oneliner(
                     new_author, self.env)
                if new_body:
                    req.hdf['discussion.body'] = wiki_to_html(new_body,
                      self.env, req)

            elif mode == 'topic-quote':
                req.perm.assert_permission('DISCUSSION_APPEND')

                # Prepare old content.
                lines = topic['body'].splitlines()
                for I in xrange(len(lines)):
                    lines[I] = '> %s' % (lines[I])
                req.hdf['args.body'] = '\n'.join(lines)

            elif mode == 'topic-post-add':
                req.perm.assert_permission('DISCUSSION_APPEND')

                # Get form values.
                new_subject = Markup(req.args.get('subject'))
                new_author = Markup(req.args.get('author'))
                new_body = Markup(req.args.get('body'))

                #�Add topic.
                self.add_topic(cursor, forum['id'], new_subject, new_author,
                  new_body)

            elif mode == 'topic-edit':
                req.perm.assert_permission('DISCUSSION_APPEND')
                if not is_moderator and (topic['author'] != req.authname):
                    raise PermissionError('Topic edit')

                # Prepare form values.
                req.hdf['args.body'] = topic['body']
                req.hdf['args.subject'] = topic['subject']

            elif mode == 'topic-post-edit':
                req.perm.assert_permission('DISCUSSION_APPEND')
                if not is_moderator and (topic['author'] != req.authname):
                    raise PermissionError('Topic edit')

                # Get form values.
                new_subject = Markup(req.args.get('subject'))
                new_body = Markup(req.args.get('body'))

                # Edit topic.
                topic['subject'] = new_subject
                topic['body'] = new_body
                self.edit_topic(cursor, topic['id'], topic['forum'],
                  new_subject, new_body)

            elif mode == 'topic-move':
                req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')

                # Display Move Topic form
                req.hdf['discussion.forums'] = self.get_forums(req, cursor)

            elif mode == 'topic-post-move':
                req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')

                # Get form values
                new_forum = req.args.get('new_forum')

                # Move topic.
                self.set_forum(cursor, topic['id'], new_forum)

            elif mode == 'topic-delete':
                req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')

                # Delete topic.
                self.delete_topic(cursor, topic['id'])

            elif mode == 'message-list':
                req.perm.assert_permission('DISCUSSION_VIEW')

                # Get form values.
                new_author = Markup(req.args.get('author'))
                new_subject = Markup(req.args.get('subject'))
                new_body = Markup(req.args.get('body'))

                # Get time when topic was visited from session.
                visited = eval(req.session.get('visited-topics') or '{}')
                if visited.has_key(topic['id']):
                    visit_time = int(visited[topic['id']])
                else:
                    visit_time = 0

                # Update this topic visit time and save to session.
                visited[topic['id']] = int(time.time())
                req.session['visited-topics'] = str(visited)

                # Mark new topic.
                if int(topic['time']) > visit_time:
                    topic['new'] = True

                # Prepare display of topic
                if new_author:
                    req.hdf['discussion.author'] = wiki_to_oneliner(
                      new_author, self.env)
                if new_subject:
                    req.hdf['discussion.subject'] = wiki_to_oneliner(
                      new_subject, self.env)
                if new_body:
                    req.hdf['discussion.body'] = wiki_to_html(new_body,
                      self.env, req)

                # Prepare display of messages
                display = req.session.get('message-list-display')
                req.hdf['discussion.display'] = display
                if display == 'flat-asc':
                    req.hdf['discussion.messages'] = self.get_flat_messages(
                      req, cursor, topic['id'], visit_time)
                elif display == 'flat-desc':
                    req.hdf['discussion.messages'] = self.get_flat_messages(
                      req, cursor, topic['id'], visit_time, 'ORDER BY time DESC')
                else:
                    req.hdf['discussion.messages'] = self.get_messages(req,
                      cursor, topic['id'], visit_time)

            elif mode == 'message-quote':
                req.perm.assert_permission('DISCUSSION_APPEND')

                # Prepare old content.
                lines = message['body'].splitlines()
                for I in xrange(len(lines)):
                    lines[I] = '> %s' % (lines[I])
                req.hdf['args.body'] = '\n'.join(lines)

            elif mode == 'message-post-add':
                req.perm.assert_permission('DISCUSSION_APPEND')

                # Get form values.
                new_author = Markup(req.args.get('author'))
                new_body = Markup(req.args.get('body'))

                #�Add message.
                if message:
                    self.add_message(cursor, forum['id'], topic['id'],
                      message['id'], new_author, new_body)
                else:
                    self.add_message(cursor, forum['id'], topic['id'], '-1',
                      new_author, new_body)

            elif mode == 'message-edit':
                req.perm.assert_permission('DISCUSSION_APPEND')
                if not is_moderator and (message['author'] != req.authname):
                    raise PermissionError('Message edit')

                # Prepare form values.
                req.hdf['args.body'] = message['body']

            elif mode == 'message-post-edit':
                req.perm.assert_permission('DISCUSSION_APPEND')
                if not is_moderator and (message['author'] != req.authname):
                    raise PermissionError('Message edit')

                # Get form values.
                new_body = Markup(req.args.get('body'))

                # Edit message.
                message['body'] = new_body
                self.edit_message(cursor, message['id'], message['forum'],
                  message['topic'], message['replyto'], new_body)

            elif mode == 'message-delete':
                req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')

                # Delete message.
                self.delete_message(cursor, message['id'])

            elif mode == 'message-set-display':
                req.perm.assert_permission('DISCUSSION_VIEW')

                # Get form values
                display = req.args.get('display')

                # Set message list display mode to session
                req.session['message-list-display'] = display

    # Get one item functions

    def get_message(self, cursor, id):
        columns = ('id', 'forum', 'topic', 'replyto', 'time', 'author', 'body')
        sql = "SELECT id, forum, topic, replyto, time, author, body FROM" \
          " message WHERE id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        for row in cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_topic(self, cursor, id):
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
        sql = "SELECT id, forum, time, subject, body, author FROM topic WHERE" \
          " id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        for row in cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_topic_by_subject(self, cursor, subject):
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
        sql = "SELECT id, forum, time, subject, body, author FROM topic WHERE" \
          " subject = '%s'" % (subject)
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_forum(self, cursor, id):
        columns = ('name', 'moderators', 'id', 'time', 'subject',
          'description', 'group')
        sql = "SELECT name, moderators, id, time, subject, description," \
          " forum_group FROM forum WHERE id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        for row in cursor:
            row = dict(zip(columns, row))
            row['moderators'] = row['moderators'].split(' ')
            return row
        return None

    def get_group(self, cursor, id):
        columns = ('id', 'name', 'description')
        sql = "SELECT id, name, description FROM forum_group WHERE id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        for row in cursor:
            row = dict(zip(columns, row))
            return row
        return {'id' : 0, 'name': 'None', 'description': 'No Group'}

    # Set item functions

    def set_group(self, cursor, forum, group):
        if not group:
            group = '0'
        sql = "UPDATE forum SET forum_group = %s WHERE id = %s"
        self.log.debug(sql % (group, forum))
        cursor.execute(sql, (group, forum))

    def set_forum(self, cursor, topic, forum):
        sql = "UPDATE topic SET forum = %s WHERE id = %s"
        self.log.debug(sql % (forum, topic))
        cursor.execute(sql, (forum, topic))
        sql = "UPDATE message SET forum = %s WHERE topic = %s"
        self.log.debug(sql % (forum, topic))
        cursor.execute(sql, (forum, topic))

    # Edit all functons

    def edit_group(self, cursor, group, name, description):
        sql = "UPDATE forum_group SET name = %s, description = %s WHERE id = %s"
        self.log.debug(sql % (name, description, group))
        cursor.execute(sql, (escape(name), escape(description), group))

    def edit_forum(self, cursor, forum, name, subject, description, moderators,
      group):
        moderators = ' '.join(moderators)
        if not group:
            group = '0'
        sql = "UPDATE forum SET name = %s, subject = %s, description = %s," \
          " moderators = %s, forum_group = %s WHERE id = %s"
        self.log.debug(sql % (name, subject, description, moderators,
          group, forum))
        cursor.execute(sql, (escape(name), escape(subject),
          escape(description), escape(moderators), group, forum))

    def edit_topic(self, cursor, topic, forum, subject, body):
        sql = "UPDATE topic SET forum = %s, subject = %s, body = %s WHERE id" \
          " = %s"
        self.log.debug(sql % (forum, subject, body, topic))
        cursor.execute(sql, (forum, escape(subject), escape(body),
          topic))

    def edit_message(self, cursor, message, forum, topic, replyto, body):
        sql = "UPDATE message SET forum = %s, topic = %s, replyto = %s, body" \
          " = %s WHERE id = %s"
        self.log.debug(sql % (forum, topic, replyto, body, message))
        cursor.execute(sql, (forum, topic, replyto, escape(body),
          message))

    # Get list functions

    def get_groups(self, req, cursor, order_by = 'ORDER BY id ASC'):
        # Get count of forums without group
        sql = "SELECT COUNT(id) FROM forum WHERE forum_group = 0"
        self.log.debug(sql)
        cursor.execute(sql)
        no_group_forums = 0
        for row in cursor:
            no_group_forums = row[0]
        groups = [{'id' : 0, 'name' : 'None', 'description' : 'No Group',
          'forums' : no_group_forums}]

        # Get forum groups
        columns = ('id', 'name', 'description', 'forums')
        sql = "SELECT id, name, description, (SELECT COUNT(id) FROM forum f" \
          " WHERE f.forum_group = forum_group.id) FROM forum_group " + order_by
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            row['name'] = wiki_to_oneliner(row['name'], self.env)
            row['description'] = wiki_to_oneliner(row['description'], self.env)
            groups.append(row)
        return groups

    def get_forums(self, req, cursor, order_by = 'ORDER BY subject ASC'):
        columns = ('id', 'name', 'author', 'time', 'moderators', 'group',
          'subject', 'description', 'topics', 'replies', 'lastreply',
          'lasttopic')
        sql = "SELECT id, name, author, time, moderators, forum_group," \
          " subject, description, (SELECT COUNT(id) FROM topic t WHERE" \
          " t.forum = forum.id) AS topics, (SELECT COUNT(id) FROM message m" \
          " WHERE m.forum = forum.id) AS replies, (SELECT MAX(time) FROM" \
          " message m WHERE m.forum = forum.id) AS lasttopic, (SELECT" \
          " MAX(time) FROM topic t WHERE t.forum = forum.id) AS lastreply" \
          " FROM forum " + order_by
        self.log.debug(sql)
        cursor.execute(sql)
        forums = []
        for row in cursor:
            row = dict(zip(columns, row))
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

    def get_topics(self, req, cursor, forum, order_by = 'ORDER BY time ASC'):
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author',
          'replies', 'lastreply')
        sql = "SELECT id, forum, time, subject, body, author, (SELECT" \
          " COUNT(id) FROM message m WHERE m.topic = topic.id) AS replies," \
          " (SELECT MAX(time) FROM message m WHERE m.topic = topic.id) AS" \
          " lastreply FROM topic WHERE forum = %s " + order_by
        self.log.debug(sql % (forum,))
        cursor.execute(sql, (forum,))
        topics = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            row['body'] = wiki_to_html(row['body'], self.env, req)
            if row['lastreply']:
                row['lastreply'] = pretty_timedelta(row['lastreply'])
            else:
                row['lastreply'] = 'No replies'
            row['time'] = format_datetime(row['time'])
            topics.append(row)
        return topics

    def get_messages(self, req, cursor, topic, time, order_by = 'ORDER BY time ASC'):
        columns = ('id', 'replyto', 'time', 'author', 'body')
        sql = "SELECT id, replyto, time, author, body FROM message WHERE" \
          " topic = %s " + order_by
        self.log.debug(sql % (topic,))
        cursor.execute(sql, (topic,))
        messagemap = {}
        messages = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            row['body'] = wiki_to_html(row['body'], self.env, req)
            if int(row['time']) > time:
                row['new'] = True
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

    def get_flat_messages(self, req, cursor, topic, time, order_by =
      'ORDER BY time ASC'):
        columns = ('id', 'replyto', 'time', 'author', 'body')
        sql = "SELECT id, replyto, time, author, body FROM message WHERE" \
          " topic = %s " + order_by
        self.log.debug(sql % (topic,))
        cursor.execute(sql, (topic,))
        messages = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            row['body'] = wiki_to_html(row['body'], self.env, req)
            if int(row['time']) > time:
                row['new'] = True
            row['time'] = format_datetime(row['time'])
            messages.append(row)
        return messages

    def get_users(self):
        users = []
        for user in self.env.get_known_users():
            users.append(user[0])
        return users

    # Add items functions

    def add_group(self, cursor, name, description):
        sql = "INSERT INTO forum_group (name, description) VALUES (%s, %s)"
        self.log.debug(sql % (name, description))
        cursor.execute(sql, (escape(name), escape(description)))

    def add_forum(self, cursor, name, author, subject, description, moderators,
      group):
        moderators = ' '.join(moderators)
        if not group:
            group = '0'
        sql = "INSERT INTO forum (name, author, time, moderators, subject," \
          " description, forum_group) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        self.log.debug(sql % (name, author, str(int(time.time())), moderators,
          subject, description, group))
        cursor.execute(sql, (escape(name), escape(author),
          str(int(time.time())), escape(moderators), escape(subject),
          escape(description), group))

    def add_topic(self, cursor, forum, subject, author, body):
        sql = "INSERT INTO topic (forum, time, author, subject, body) VALUES" \
          " (%s, %s, %s, %s, %s)"
        self.log.debug(sql % (forum, int(time.time()), author, subject, body))
        cursor.execute(sql, (forum, int(time.time()), escape(author),
          escape(subject), escape(body)))

    def add_message(self, cursor, forum, topic, replyto, author, body):
        sql = "INSERT INTO message (forum, topic, replyto, time, author," \
          " body) VALUES (%s, %s, %s, %s, %s, %s)"
        self.log.debug(sql % (forum, topic, replyto, int(time.time()),
          author, body))
        cursor.execute(sql, (forum, topic, replyto, int(time.time()),
          escape(author), escape(body)))

    # Delete items functions

    def delete_group(self, cursor, group):
        sql = "DELETE FROM forum_group WHERE id = %s"
        self.log.debug(sql % (group,))
        cursor.execute(sql, (group,))
        sql = "UPDATE forum SET forum_group = 0 WHERE forum_group = %s"
        self.log.debug(sql % (group,))
        cursor.execute(sql, (group,))

    def delete_forum(self, cursor, forum):
        sql = "DELETE FROM message WHERE forum = %s"
        self.log.debug(sql % (forum,))
        cursor.execute(sql, (forum,))
        sql = "DELETE FROM topic WHERE forum = %s"
        self.log.debug(sql % (forum,))
        cursor.execute(sql, (forum,))
        sql = "DELETE FROM forum WHERE id = %s"
        self.log.debug(sql % (forum,))
        cursor.execute(sql, (forum,))

    def delete_topic(self, cursor, topic):
        sql = "DELETE FROM message WHERE topic = %s"
        self.log.debug(sql % (topic,))
        cursor.execute(sql, (topic,))
        sql = "DELETE FROM topic WHERE id = %s"
        self.log.debug(sql % (topic,))
        cursor.execute(sql, (topic,))

    def delete_message(self, cursor, message):
        # Get message replies
        sql = "SELECT id FROM message WHERE replyto = %s"
        self.log.debug(sql % (message,))
        cursor.execute(sql, (message,))
        replies = []
        for row in cursor:
            replies.append(row[0])

        # Delete all replies
        for reply in replies:
            self.delete_message(cursor, reply)

        # Delete message itself
        sql = "DELETE FROM message WHERE id = %s"
        self.log.debug(sql % (message,))
        cursor.execute(sql, (message,))
