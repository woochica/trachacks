# -*- coding: utf-8 -*-

# General includes.
from datetime import *

# Trac includes.
from trac.core import *
from trac.mimeview import Context
from trac.perm import PermissionError
from trac.web.chrome import add_stylesheet, add_script, add_ctxtnav
from trac.web.href import Href
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util.datefmt import to_timestamp, to_datetime, utc, \
  format_datetime, pretty_timedelta
from trac.util.html import html
from trac.util.text import to_unicode

# Genshi includes.
from genshi.input import HTML
from genshi.core import Markup
from genshi.filters import Transformer

class IDiscussionFilter(Interface):
    """Extension point interface for components that want to filter discussion
    topics and messages before their addition."""

    def filter_topic(req, topic):
        """ Called before new topic creation. May return tuple (False,
        <error_message>) or (True, <topic>) where <error_message> is a message
        that will be displayed when topic creation will be canceled and <topic>
        is modified topic that will be added."""

    def filter_message(req, message):
        """ Called before new message creation. May return tuple (False,
        <error_message>) or (True, <message>) where <error_message> is a
        message that will be displayed when message creation will be canceled
        and <message> is modified message that will be added."""


class ITopicChangeListener(Interface):
    """Extension point interface for components that require notification
    when new forum topics are created, modified or deleted."""

    def topic_created(topic):
        """Called when a topic is created. Only argument `topic` is
        a dictionary with topic attributes."""

    def topic_changed(topic, old_topic):
        """Called when a topic is modified. `old_topic` is a dictionary
        containing the previous values of the topic attributes and `topic` is
        a dictionary with new values that has changed."""

    def topic_deleted(topic):
        """Called when a topic is deleted. `topic` argument is a dictionary
        with values of attributes of just deleted topic."""

class IMessageChangeListener(Interface):
    """Extension point interface for components that require notification
    when new forum messages are created, modified or deleted."""

    def message_created(message):
        """Called when a message is created. Only argument `message` is
        a dictionary with message attributes."""

    def message_changed(message, old_message):
        """Called when a message is modified. `old_message` is a dictionary
        containing the previous values of the message attributes and `message`
        is a dictionary with new values that has changed."""

    def message_deleted(message):
        """Called when a message is deleted. `message` argument is a dictionary
        with values of attributes of just deleted message."""

class DiscussionApi(Component):

    # Extension points.
    topic_change_listeners = ExtensionPoint(ITopicChangeListener)
    message_change_listeners = ExtensionPoint(IMessageChangeListener)
    discussion_filters = ExtensionPoint(IDiscussionFilter)

    # Main request processing function.
    def process_discussion(self, context):
        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Get request items and actions.
        self._prepare_context(context)
        actions = self._get_actions(context)
        self.log.debug('actions: %s' % (actions,))

        # Get session data.
        context.visited_forums = eval(context.req.session.get('visited-forums')
          or '{}')
        context.visited_topics = eval(context.req.session.get('visited-topics')
          or '{}')

        # Perform actions.
        self._do_actions(context, actions)

        # Update session data.
        context.req.session['visited-topics'] = to_unicode(context.visited_topics)
        context.req.session['visited-forums'] = to_unicode(context.visited_forums)

        # Fill up template data structure.
        context.data['moderator'] = context.moderator
        context.data['group'] = context.group
        context.data['forum'] = context.forum
        context.data['topic'] = context.topic
        context.data['message'] = context.message
        context.data['mode'] = actions[-1]
        context.data['time'] = datetime.now(utc)
        context.data['realm'] = context.resource.realm
        context.data['env'] = self.env

        # Commit database changes.
        db.commit()

        # Add context navigation.
        if context.forum:
            add_ctxtnav(context.req, 'Forum Index',
              context.req.href.discussion())
        if context.topic:
            add_ctxtnav(context.req, format_to_oneliner_no_links(self.env,
              context, context.forum['name']), context.req.href.discussion(
              'forum', context.forum['id']), context.forum['name'])
        if context.message:
            add_ctxtnav(context.req, format_to_oneliner_no_links(self.env,
              context, context.topic['subject']), context.req.href.discussion(
              'topic', context.topic['id']), context.topic['subject'])

        # Add CSS styles and scripts.
        add_stylesheet(context.req, 'common/css/wiki.css')
        add_stylesheet(context.req, 'discussion/css/discussion.css')
        add_stylesheet(context.req, 'discussion/css/admin.css')
        add_script(context.req, 'common/js/trac.js')
        add_script(context.req, 'common/js/search.js')
        add_script(context.req, 'common/js/wikitoolbar.js')

        # Return request template and data.
        self.env.log.debug(context.data)
        return actions[-1] + '.html', {'discussion' : context.data}

    def _prepare_context(self, context):
        # Prepare template data.
        context.data = {}

        context.group = None
        context.forum = None
        context.topic = None
        context.message = None
        context.redirect_url = None

        # Populate active message.
        if context.req.args.has_key('message'):
            message_id = int(context.req.args.get('message') or 0)
            context.message = self.get_message(context, message_id)
            if context.message:
                context.topic = self.get_topic(context, context.message['topic'])
                context.forum = self.get_forum(context, context.topic['forum'])
                context.group = self.get_group(context, context.forum[
                  'forum_group'])
            else:
                raise TracError('Message with ID %s does not exist.' % (
                  message_id,))

        # Populate active topic.
        elif context.req.args.has_key('topic'):
            topic_id = int(context.req.args.get('topic') or 0)
            context.topic = self.get_topic(context, topic_id)
            if context.topic:
                context.forum = self.get_forum(context, context.topic['forum'])
                context.group = self.get_group(context, context.forum[
                  'forum_group'])
            else:
                raise TracError('Topic with ID %s does not exist.' % (
                  topic_id,))

        # Populate active forum.
        elif context.req.args.has_key('forum'):
            forum_id = int(context.req.args.get('forum') or 0)
            context.forum = self.get_forum(context, forum_id)
            if context.forum:
                context.group = self.get_group(context, context.forum[
                  'forum_group'])
            else:
                raise TracError('Forum with ID %s does not exist.' % (
                  forum_id,))

        # Populate active group.
        elif context.req.args.has_key('group'):
            group_id = int(context.req.args.get('group') or 0)
            context.group = self.get_group(context, group_id)
            if not context.group:
                raise TracError('Group with ID %s does not exist.' % (
                  group_id,))

        # Determine moderator rights.
        context.moderator = context.forum and (context.req.authname in
          context.forum['moderators']) or context.req.perm.has_permission(
          'DISCUSSION_ADMIN')

    def _get_actions(self, context):
        # Get action.
        action = context.req.args.get('discussion_action')
        preview = context.req.args.has_key('preview');
        submit = context.req.args.has_key('submit');
        self.log.debug('realm: %s, action: %s, preview: %s, submit: %s' % (
          context.resource.realm, action, preview, submit))

        # Determine mode.
        if context.message:
            if context.resource.realm == 'discussion-admin':
                pass
            elif context.resource.realm == 'discussion-wiki':
                if action == 'add':
                    return ['message-add', 'wiki-message-list']
                elif action == 'quote':
                    return ['message-quote', 'wiki-message-list']
                elif action == 'post-add':
                    if preview:
                        return ['wiki-message-list']
                    else:
                        return ['message-post-add']
                elif action == 'edit':
                    return ['message-edit', 'wiki-message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['wiki-message-list']
                    else:
                        return ['message-post-edit']
                elif action == 'delete':
                    return ['message-delete']
                elif action == 'set-display':
                    return ['message-set-display', 'wiki-message-list']
                else:
                    return ['wiki-message-list']
            else:
                if action == 'add':
                    return ['message-add', 'message-list']
                elif action == 'quote':
                    return ['message-quote', 'message-list']
                elif action == 'post-add':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-add']
                elif action == 'edit':
                    return ['message-edit', 'message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-edit']
                elif action == 'delete':
                    return ['message-delete']
                elif action == 'set-display':
                    return ['message-set-display', 'message-list']
                else:
                    return ['message-list']
        if context.topic:
            if context.resource.realm == 'discussion-admin':
                pass
            elif context.resource.realm == 'discussion-wiki':
                if action == 'add':
                    return ['message-add', 'wiki-message-list']
                elif action == 'quote':
                    return ['topic-quote','wiki-message-list']
                elif action == 'post-add':
                    if preview:
                        return ['wiki-message-list']
                    else:
                        return ['message-post-add']
                elif action == 'edit':
                    return ['topic-edit', 'wiki-message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['wiki-message-list']
                    else:
                        return ['topic-post-edit']
                elif action == 'set-display':
                    return ['message-set-display', 'wiki-message-list']
                else:
                    return ['wiki-message-list']
            else:
                if action == 'add':
                    return ['message-add', 'message-list']
                elif action == 'quote':
                    return ['topic-quote', 'message-list']
                elif action == 'post-add':
                    if preview:
                        return ['message-list']
                    else:
                        return ['message-post-add']
                elif action == 'edit':
                    return ['topic-edit', 'message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['message-list']
                    else:
                        return ['topic-post-edit']
                elif action == 'delete':
                    return ['topic-delete']
                elif action == 'move':
                    return ['topic-move']
                elif action == 'post-move':
                    return ['topic-post-move']
                elif action == 'set-display':
                    return ['message-set-display', 'message-list']
                else:
                    return ['message-list']
        elif context.forum:
            if context.resource.realm == 'discussion-admin':
                if action == 'post-edit':
                    return ['forum-post-edit']
                else:
                    return ['admin-forum-list']
            elif context.resource.realm == 'discussion-wiki':
                return ['wiki-message-list']
            else:
                if action == 'add':
                    return ['topic-add']
                elif action == 'post-add':
                    if preview:
                        return ['topic-add']
                    else:
                        return ['topic-post-add']
                elif action == 'delete':
                    return ['forum-delete']
                else:
                    return ['topic-list']
        elif context.group:
            if context.resource.realm == 'discussion-admin':
                if action == 'post-add':
                    return ['forum-post-add']
                elif action == 'post-edit':
                    return ['group-post-edit']
                elif action == 'delete':
                    return ['forums-delete']
                else:
                    if context.group['id']:
                        return ['admin-group-list']
                    else:
                        return ['admin-forum-list']
            elif context.resource.realm == 'discussion-wiki':
                return ['wiki-message-list']
            else:
                if action == 'post-add':
                    return ['forum-post-add']
                else:
                    return ['forum-list']
        else:
            if context.resource.realm == 'discussion-admin':
                if action == 'post-add':
                    return ['group-post-add']
                elif action == 'delete':
                    return ['groups-delete']
                else:
                    return ['admin-group-list']
            elif context.resource.realm == 'discussion-wiki':
                return ['wiki-message-list']
            else:
                if action == 'add':
                    return ['forum-add']
                elif action == 'post-add':
                    return ['forum-post-add']
                else:
                    return ['forum-list']

    def _do_actions(self, context, actions):
        for action in actions:
            if action == 'group-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Display groups.
                context.data['groups'] = self.get_groups(context)

            elif action == 'admin-group-list':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')

                # Display groups.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['groups'] = self.get_groups(context, order, desc)

            elif action == 'group-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

            elif action == 'group-post-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                group = {'name' : context.req.args.get('name'),
                         'description' : context.req.args.get('description')}

                # Add new group.
                self.add_group(context, group)

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'group-post-edit':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                group = {'name' : context.req.args.get('name'),
                         'description' : context.req.args.get('description')}

                # Edit group.
                self.edit_group(context, context.group['id'], group)

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'group-delete':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'groups-delete':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get selected groups.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete selected groups.
                if selection:
                    for group_id in selection:
                        self.delete_group(context, int(group_id))

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'forum-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Get form values.
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')

                # Display forums.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['groups'] = self.get_groups(context)
                context.data['forums'] = self.get_forums(context, order, desc)

            elif action == 'admin-forum-list':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get ordering arguments values.
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')

                # Display forums.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['users'] = self.get_users(context)
                context.data['groups'] = self.get_groups(context)
                context.data['forums'] = self.get_forums(context, order, desc)

            elif action == 'forum-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Display Add Forum form.
                context.data['users'] = self.get_users(context)
                context.data['groups'] = self.get_groups(context)

            elif action == 'forum-post-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values
                forum = {'name' : context.req.args.get('name'),
                         'author' : context.req.authname,
                         'subject' : context.req.args.get('subject'),
                         'description' : context.req.args.get('description'),
                         'moderators' : context.req.args.get('moderators'),
                         'forum_group' : int(context.req.args.get('group') or 0),
                         'time': to_timestamp(datetime.now(utc))}

                # Fix moderators attribute to be a list.
                if not forum['moderators']:
                    forum['moderators'] = []
                if not isinstance(forum['moderators'], list):
                     forum['moderators'] = [forum['moderators']]

                # Perform new forum add.
                self.add_forum(context, forum)

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'forum-post-edit':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                forum = {'name' : context.req.args.get('name'),
                         'subject' : context.req.args.get('subject'),
                         'description' : context.req.args.get('description'),
                         'moderators' : context.req.args.get('moderators'),
                         'forum_group' : int(context.req.args.get('group') or 0)}

                # Fix moderators attribute to be a list.
                if not forum['moderators']:
                    forum['moderators'] = []
                if not isinstance(forum['moderators'], list):
                     forum['moderators'] = [forum['moderators']]

                # Perform forum edit.
                self.edit_forum(context, context.forum['id'], forum)

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'forum-delete':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Delete forum.
                self.delete_forum(context, context.forum['id'])

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'forums-delete':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get selected forums.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete selected forums.
                if selection:
                    for forum_id in selection:
                        self.delete_forum(context, int(forum_id))

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'topic-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Update this forum visit time.
                context.visited_forums[context.forum['id']] = to_timestamp(
                  datetime.now(utc))

                # Get form values
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')

                # Display topics.
                context.data['order'] = order
                context.data['desc'] = desc
                context.data['topics'] = self.get_topics(context,
                  context.forum['id'], order, desc)

            elif action == 'topic-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

            elif action == 'topic-quote':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

                # Prepare old content.
                lines = context.topic['body'].splitlines()
                for I in xrange(len(lines)):
                    lines[I] = '> %s' % (lines[I])
                context.req.args['body'] = '\n'.join(lines)

            elif action == 'topic-post-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

                # Get form values.
                topic = {'forum' : context.forum['id'],
                         'subject' : context.req.args.get('subject'),
                         'author' : context.req.args.get('author'),
                         'body' : context.req.args.get('body'),
                         'time': to_timestamp(datetime.now(utc))}

                # Add new topic.
                self.add_topic(context, topic)

                # Get inserted topic with new ID.
                context.topic = self.get_topic_by_time(context, topic['time'])

                # Notify change listeners.
                for listener in self.topic_change_listeners:
                    listener.topic_created(context.topic)

                # Redirect request to prevent re-submit.
                if context.resource.realm != 'discussion-wiki':
                    href = Href('discussion')
                    context.redirect_url = href('topic', context.topic['id'])
                else:
                    context.redirect_url = context.req.path_info

            elif action == 'topic-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND')
                if not context.moderator and (context.topic['author'] !=
                  context.req.authname):
                    raise PermissionError('Topic edit')

                # Prepare form values.
                context.req.args['subject'] = context.topic['subject']
                context.req.args['body'] = context.topic['body']

            elif action == 'topic-post-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND')
                if not context.moderator and (context.topic['author'] !=
                  context.req.authname):
                    raise PermissionError('Topic edit')

                # Get form values.
                topic = {'subject' : context.req.args.get('subject'),
                         'body' : context.req.args.get('body')}

                # Edit topic.
                self.edit_topic(context, context.topic['id'], topic)

                # Notify change listeners.
                for listener in self.topic_change_listeners:
                    listener.topic_changed(topic, context.topic)

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'topic-move':
                context.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Display Move Topic form.
                context.data['forums'] = self.get_forums(context)

            elif action == 'topic-post-move':
                context.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Get form values.
                forum_id = int(context.req.args.get('new_forum') or 0)

                # Move topic.
                self.set_forum(context, context.topic['id'], forum_id)

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'topic-delete':
                context.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Delete topic.
                self.delete_topic(context, context.topic['id'])

                # Notify change listeners.
                for listener in self.topic_change_listeners:
                    listener.topic_deleted(context.topic)

                # Redirect request to prevent re-submit.
                if context.resource.realm != 'discussion-wiki':
                    href = Href('discussion')
                    context.redirect_url = href('forum', context.topic['forum'])
                else:
                    context.redirect_url = req.path_info

            elif action == 'message-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW')
                self._prepare_message_list(context, context.topic)

            elif action == 'wiki-message-list':
                if context.topic:
                    self._prepare_message_list(context, context.topic)

            elif action == 'message-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

            elif action == 'message-quote':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

                # Prepare old content.
                lines = context.message['body'].splitlines()
                for I in xrange(len(lines)):
                    lines[I] = '> %s' % (lines[I])
                context.req.args['body'] = '\n'.join(lines)

            elif action == 'message-post-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

                # Get form values.
                message = {'forum' : context.forum['id'],
                           'topic' : context.topic['id'],
                           'replyto' : context.message and context.message['id']
                              or -1,
                           'author' : context.req.args.get('author'),
                           'body' : context.req.args.get('body'),
                           'time' : to_timestamp(datetime.now(utc))}

                # Add message.
                self.add_message(context, message)

                # Get inserted message with new ID.
                context.message = self.get_message_by_time(context,
                  message['time'])

                # Notify change listeners.
                for listener in self.message_change_listeners:
                    listener.message_created(context.message)

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'message-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND')
                if not context.moderator and (context.message['author'] !=
                  context.req.authname):
                    raise PermissionError('Message edit')

                # Prepare form values.
                context.req.args['body'] = context.message['body']

            elif action == 'message-post-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND')
                if not context.moderator and (context.message['author'] !=
                  context.req.authname):
                    raise PermissionError('Message edit')

                # Get form values.
                message = {'body' : context.req.args.get('body')}

                # Edit message.
                self.edit_message(context, context.message['id'], message)

                # Notify change listeners.
                for listener in self.message_change_listeners:
                    listener.message_changed(message, message.topic)

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'message-delete':
                context.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not context.moderator:
                    raise PermissionError('Forum moderate')

                # Delete message.
                self.delete_message(context, context.message['id'])

                # Notify change listeners.
                for listener in self.message_change_listeners:
                    listener.message_deleted(context.message)

                # Redirect request to prevent re-submit.
                context.redirect_url = context.req.path_info

            elif action == 'message-set-display':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Get form values.
                display = context.req.args.get('display')

                # Set message list display mode to session.
                context.req.session['message-list-display'] = display

        # Redirection is not necessary.
        return None

    def _prepare_message_list(self, context, topic):
        # Get time when topic was visited from session.
        visit_time = int(context.visited_topics.has_key(topic['id']) and
          (context.visited_topics[topic['id']] or 0))

        # Update this topic visit time.
        context.visited_topics[topic['id']] = to_timestamp(datetime.now(utc))

        # Get topic messages.
        display = context.req.session.get('message-list-display')
        if display == 'flat-asc':
             messages = self.get_flat_messages(context, topic['id'])
        elif display == 'flat-desc':
             messages = self.get_flat_messages(context, topic['id'], desc =
               True)
        else:
             messages = self.get_messages(context, topic['id'])

        # Prepare display of messages.
        context.data['visit_time'] = visit_time
        context.data['display'] = display
        context.data['messages'] = messages

    # Get one item functions.

    def _get_item(self, context, table, columns, where = '', values = ()):
        sql = 'SELECT ' + ', '.join(columns) + ' FROM ' + table + (where
          and (' WHERE ' + where) or '')
        self.log.debug(sql % values)
        context.cursor.execute(sql, values)
        for row in context.cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_message(self, context, id):
        # Get message by ID.
        return self._get_item(context, 'message', ('id', 'forum', 'topic',
          'replyto', 'time', 'author', 'body'), 'id = %s', (id,))

    def get_message_by_time(self, context, time):
        # Get message by time of creation.
        return self._get_item(context, 'message', ('id', 'forum', 'topic',
          'replyto', 'time', 'author', 'body'), 'time = %s', (time,))

    def get_topic(self, context, id):
        # Get topic by ID.
        return self._get_item(context, 'topic', ('id', 'forum', 'subject',
          'time', 'author', 'body'), 'id = %s', (id,))

    def get_topic_by_time(self, context, time):
        # Get topic by time of creation.
        return self._get_item(context, 'topic', ('id', 'forum', 'subject',
          'time', 'author', 'body'), 'time = %s', (time,))

    def get_topic_by_subject(self, context, subject):
        # Get topic by subject.
        return self._get_item(context, 'topic', ('id', 'forum', 'subject',
          'time', 'author', 'body'), 'subject = %s', (subject,))

    def get_forum(self, context, id):
        # Get forum by ID.
        forum = self._get_item(context, 'forum', ('id', 'forum_group', 'name',
          'subject', 'time', 'moderators', 'description'), 'id = %s', (id,))

        # Fix list of moderators.
        if forum:
           forum['moderators'] = forum['moderators'].split(' ')

        return forum

    def get_group(self, context, id):
        # Get forum group or none group.
        return self._get_item(context, 'forum_group', ('id', 'name',
          'description'), 'id = %s', (id,)) or {'id' : 0, 'name': 'None',
          'description': 'No Group'}

    # Get list functions.

    def _get_items(self, context, table, columns, where = '', values = (),
      order_by = '', desc = False):
        sql = 'SELECT ' + ', '.join(columns) + ' FROM ' + table + (where
          and (' WHERE ' + where) or '') + (order_by and (' ORDER BY ' +
          order_by + (' ASC', ' DESC')[bool(desc)]) or '')
        self.log.debug(sql % values)
        context.cursor.execute(sql, values)
        items = []
        for row in context.cursor:
            row = dict(zip(columns, row))
            items.append(row)
        return items

    def get_groups(self, context, order_by = 'id', desc = False):
        # Get count of forums without group.
        sql = "SELECT COUNT(f.id) FROM forum f WHERE f.forum_group = 0"
        self.env.log.debug(sql)
        context.cursor.execute(sql)
        no_group_forums = 0
        for row in context.cursor:
            no_group_forums = row[0]
        groups = [{'id' : 0, 'name' : 'None', 'description' : 'No Group',
          'forums' : no_group_forums}]

        # Get forum groups.
        if order_by != 'forum':
            order_by = 'g.' + order_by
        columns = ('id', 'name', 'description', 'forums')
        sql = "SELECT g.id, g.name, g.description, f.forums FROM " \
          " forum_group g LEFT JOIN (SELECT COUNT(id) AS forums, " \
          " forum_group FROM forum GROUP BY forum_group) f ON g.id = " \
          " f.forum_group ORDER BY " + order_by + (" ASC",
          " DESC")[bool(desc)]
        self.env.log.debug(sql)
        context.cursor.execute(sql)
        for row in context.cursor:
            row = dict(zip(columns, row))
            groups.append(row)
        return groups

    def get_forums(self, context, order_by = 'subject', desc = False):

        def _get_new_topic_count(context, forum_id):
           time = int(context.visited_forums.has_key(forum_id) and
             (context.visited_forums[forum_id] or 0))
           sql = "SELECT COUNT(id) FROM topic t WHERE t.forum = %s AND t.time > %s"

           self.env.log.debug(sql % (forum_id, time))
           context.cursor.execute(sql, (forum_id, time))
           for row in context.cursor:
              return int(row[0])
           return 0

        def _get_new_replies_count(context, forum_id):
           sql = "SELECT id FROM topic t WHERE t.forum = %s"
           self.env.log.debug(sql % (forum_id,))
           context.cursor.execute(sql, (forum_id,))

           # Get IDs of topics in this forum.
           topics = []
           for row in context.cursor:
               topics.append(row[0])

           # Count unseen messages.
           count = 0
           for topic_id in topics:
               time = int(context.visited_topics.has_key(topic_id) and
                 (context.visited_topics[topic_id] or 0))
               sql = "SELECT COUNT(id) FROM message m WHERE m.topic = %s AND m.time > %s"
               self.env.log.debug(sql % (topic_id, time))
               context.cursor.execute(sql, (topic_id, time))
               for row in context.cursor:
                   count += int(row[0])

           return count

        if not order_by in ('topics', 'replies', 'lasttopic', 'lastreply'):
            order_by = 'f.' + order_by
        columns = ('id', 'name', 'author', 'time', 'moderators', 'forum_group',
          'subject', 'description', 'topics', 'replies', 'lasttopic',
          'lastreply')
        sql = "SELECT f.id, f.name, f.author, f.time, f.moderators, " \
          "f.forum_group, f.subject, f.description, ta.topics, ta.replies, " \
          "ta.lasttopic, ta.lastreply FROM forum f LEFT JOIN (SELECT " \
          "COUNT(t.id) AS topics, MAX(t.time) AS lasttopic, SUM(ma.replies) " \
          "AS replies, MAX(ma.lastreply) AS lastreply, t.forum AS forum FROM " \
          " topic t LEFT JOIN (SELECT COUNT(m.id) AS replies, MAX(m.time) AS " \
          "lastreply, m.topic AS topic FROM message m GROUP BY m.topic) ma ON " \
          "t.id = ma.topic GROUP BY forum) ta ON f.id = ta.forum ORDER BY " + \
          order_by + (" ASC", " DESC")[bool(desc)]
        self.env.log.debug(sql)
        context.cursor.execute(sql)

        # Convert certain forum attributes.
        forums = []
        for row in context.cursor:
            row = dict(zip(columns, row))
            forums.append(row)

        # Compute count of new replies and topics.
        for forum in forums:
            forum['new_topics'] = _get_new_topic_count(context, forum['id'])
            forum['new_replies'] = _get_new_replies_count(context, forum['id'])

        return forums

    def get_topics(self, context, forum_id, order_by = 'time', desc = False):

        def _get_new_replies_count(context, topic_id):
            time = int(context.visited_topics.has_key(topic_id) and
              (context.visited_topics[topic_id] or 0))
            sql = "SELECT COUNT(id) FROM message m WHERE m.topic = %s AND m.time > %s"

            self.env.log.debug(sql % (topic_id, time))
            context.cursor.execute(sql, (topic_id, time))
            for row in context.cursor:
               return int(row[0])
            return 0

        if not order_by in ('replies', 'lastreply',):
            order_by = 't.' + order_by
        columns = ('id', 'forum', 'time', 'subject', 'body', 'author',
          'replies', 'lastreply')
        sql = "SELECT t.id, t.forum, t.time, t.subject, t.body, t.author," \
          " m.replies, m.lastreply FROM topic t LEFT JOIN (SELECT COUNT(id)" \
          " AS replies, MAX(time) AS lastreply, topic FROM message GROUP BY" \
          " topic) m ON t.id = m.topic WHERE t.forum = %s ORDER BY " \
          + order_by + (" ASC", " DESC")[bool(desc)]
        self.env.log.debug(sql % (to_unicode(forum_id),))
        context.cursor.execute(sql, (to_unicode(forum_id),))

        # Convert certain topic attributes.
        topics = []
        for row in context.cursor:
            row = dict(zip(columns, row))
            topics.append(row)

        # Compute count of new replies.
        for topic in topics:
            topic['new_replies'] = _get_new_replies_count(context, topic['id'])

        return topics

    def get_messages(self, context, topic_id, order_by = 'time', desc = False):
        order_by = 'm.' + order_by
        columns = ('id', 'replyto', 'time', 'author', 'body')
        sql = "SELECT m.id, m.replyto, m.time, m.author, m.body FROM message m WHERE" \
          " m.topic = %s ORDER BY " + order_by + (" ASC", " DESC")[bool(desc)]
        self.env.log.debug(sql % (to_unicode(topic_id),))
        context.cursor.execute(sql, (to_unicode(topic_id),))
        messagemap = {}
        messages = []
        for row in context.cursor:
            row = dict(zip(columns, row))
            messagemap[row['id']] = row

            # Add top-level messages to the main list, in order of time.
            if row['replyto'] == -1:
                messages.append(row)

        # Second pass, add replies.
        for message in messagemap.values():
            if message['replyto'] != -1:
                parent = messagemap[message['replyto']]
                if 'replies' in parent:
                    parent['replies'].append(message)
                else:
                    parent['replies'] = [message]
        return messages;

    def get_flat_messages(self, context, id, order_by = 'time', desc = False):
        # Return messages of specified topic.
        return self._get_items(context, 'message', ('id', 'replyto', 'time',
          'author', 'body'), 'topic = %s', (id,), order_by, desc)

    def get_replies(self, context, id, order_by = 'time', desc = False):
        # Return replies of specified message.
        return self._get_items(context, 'message', ('id', 'replyto', 'time',
          'author', 'body'), where = 'replyto = %s', values = (id,), order_by
          = order_by, desc = desc)

    def get_users(self, context):
        # Return users that Trac knows.
        users = []
        for user in self.env.get_known_users():
            users.append(user[0])
        return users

    # Add items functions.

    def _add_item(self, context, table, item):
        fields = item.keys()
        values = item.values()
        sql = "INSERT INTO %s (" % (table,) + ", ".join(fields) + ") VALUES (" \
          + ", ".join(["%s" for I in xrange(len(fields))]) + ")"
        self.log.debug(sql % tuple(values))
        context.cursor.execute(sql, tuple(values))

    def add_group(self, context, group):
        self._add_item(context, 'forum_group', group)

    def add_forum(self, context, forum):
        # Fix forum fields.
        forum['moderators'] = ' '.join(forum['moderators'])

        # Add forum.
        self._add_item(context, 'forum', forum)

    def add_topic(self, context, topic):
        self._add_item(context, 'topic', topic)

    def add_message(self, context, message):
        self._add_item(context, 'message', message)

    # Delete items functions.

    def _delete_item(self, context, table, where = '', values = ()):
        sql = 'DELETE FROM ' + table + (where and (' WHERE ' + where) or '')
        self.env.log.debug(sql % values)
        context.cursor.execute(sql, values)

    def delete_group(self, context, id):
        # Delete group.
        self._delete_item(context, 'forum_group', 'id = %s', (id,))

        # Assing forums of this group to none group.
        self._set_item(context, 'forum', 'forum_group', '0', 'forum_group = %s',
          (id,))

    def delete_forum(self, context, id):
        # Delete all messages of this forum.
        self._delete_item(context, 'message', 'forum = %s', (id,))

        # Delete all topics of this forum.
        self._delete_item(context, 'topic', 'forum = %s', (id,))

        # Finally delete forum.
        self._delete_item(context, 'forum', 'id = %s', (id,))

    def delete_topic(self, context, id):
        # Delete all messages of this topic.
        self._delete_item(context, 'message', 'topic = %s', (id,))

        # Delete topic itself.
        self._delete_item(context, 'topic', 'id = %s', (id,))

    def delete_message(self, context, id):
        # Delete all replies of this message.
        for reply in self.get_replies(context, id):
            self.delete_message(context, reply['id'])

        # Delete message itself.
        self._delete_item(context, 'message', 'id = %s', (id,))

    # Set item functions.

    def _set_item(self, context, table, field, value, where = '', values = ()):
        sql = 'UPDATE ' + table + ' SET ' + field + ' = "' + to_unicode(value) \
          + '"' + (where and (' WHERE ' + where) or '')
        self.env.log.debug(sql % values)
        context.cursor.execute(sql, values)

    def set_group(self, context, forum_id, group_id):
        # Change group of specified forum.
        self._set_item(context, 'forum', 'forum_group', group_id or '0',
          'id = %s', (forum_id,))

    def set_forum(self, context, topic_id, forum_id):
        # Change forum of all topics and messages.
        self._set_item(context, 'topic', 'forum', forum_id, 'id = %s',
          (topic_id,))
        self._set_item(context, 'message', 'forum', forum_id, 'topic = %s',
          (topic_id,))

    # Edit functions.

    def _edit_item(self, context, table, id, item):
        fields = item.keys()
        values = item.values()
        sql = "UPDATE %s SET " % (table,) + ", ".join([("%s = %%s" % (field))
          for field in fields]) + " WHERE id = %s"
        self.log.debug(sql % tuple(values + [id]))
        context.cursor.execute(sql, tuple(values + [id]))

    def edit_group(self, context, id, group):
        # Edit froum group.
        self._edit_item(context, 'forum_group', id, group)

    def edit_forum(self, context, id, forum):
        # Fix forum fields.
        forum['moderators'] = ' '.join(forum['moderators'])

        # Edit forum.
        self._edit_item(context, 'forum', id, forum)

    def edit_topic(self, context, id, topic):
        # Edit topic.
        self._edit_item(context, 'topic', id, topic)

    def edit_message(self, context, id, message):
        # Edit message,
        self._edit_item(context, 'message', id, message)

# Formats wiki text to signle line HTML but removes all links.
def format_to_oneliner_no_links(env, context, content):
    stream = HTML(format_to_oneliner(env, context, content))
    return Markup(stream | Transformer('//a').unwrap())
