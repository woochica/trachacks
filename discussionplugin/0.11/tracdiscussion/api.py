# -*- coding: utf8 -*-

from datetime import *

from trac.core import *
from trac.perm import PermissionError
from trac.web.chrome import add_stylesheet, add_script, add_ctxtnav
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util.datefmt import to_timestamp, to_datetime, utc, \
  format_datetime, pretty_timedelta
from trac.util.html import html
from trac.util.text import to_unicode

from genshi.template import TemplateLoader

from tracdiscussion.notification import *

class DiscussionApi(Component):

    # Main request processing function.

    def process_discussion(self, context):
        # Clear data for next request.
        self.data = {}

        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Get request items and modes.
        group, forum, topic, message = self._get_items(context)
        modes = self._get_modes(context, group, forum, topic, message)
        self.log.debug(modes)

        # Determine moderator rights.
        is_moderator = forum and (context.req.authname in forum['moderators']) \
          or context.req.perm.has_permission('DISCUSSION_ADMIN')

        # Get session data.
        context.visited_forums = eval(context.req.session.get('visited-forums')
          or '{}')
        context.visited_topics = eval(context.req.session.get('visited-topics')
          or '{}')

        # Perform mode actions.
        self._do_action(context, modes, group, forum, topic, message,
          is_moderator)

        # Update session data.
        context.req.session['visited-topics'] = to_unicode(context.visited_topics)
        context.req.session['visited-forums'] = to_unicode(context.visited_forums)

        # Convert group, forum topic and message values for pressentation.
        if group:
            group['name'] = format_to_oneliner(self.env, context, group['name'])
            group['description'] = format_to_oneliner(self.env, context,
              group['description'])
        if forum:
            forum['name'] = format_to_oneliner(self.env, context, forum['name'])
            forum['subject'] = format_to_oneliner(self.env,context,
              forum['subject'])
            forum['description'] = format_to_oneliner(self.env, context,
              forum['description'])
            forum['time'] = format_datetime(forum['time'])
        if topic:
            topic['subject'] = format_to_oneliner(self.env, context,
              topic['subject'])
            topic['body'] = format_to_html(self.env, context, topic['body'])
            topic['author'] = format_to_oneliner(self.env, context,
              topic['author'])
            topic['time'] = format_datetime(topic['time'])
        if message:
            message['author'] = format_to_oneliner(self.env, context,
              message['author'])
            message['body'] = format_to_html(self.env, context, message['body'])
            message['time'] = format_datetime(message['time'])

        # Fill up template data structure.
        self.data['authname'] = context.req.authname
        self.data['is_moderator'] = is_moderator
        self.data['group'] = group
        self.data['forum'] = forum
        self.data['topic'] = topic
        self.data['message'] = message
        self.data['mode'] = modes[-1]
        self.data['time'] = format_datetime(datetime.now(utc))
        self.data['realm'] = context.resource.realm

        # Add context navigation.
        if forum:
            add_ctxtnav(context.req, 'Forum Index',
              context.req.href.discussion())
        if topic:
            add_ctxtnav(context.req, forum['name'],
              context.req.href.discussion(forum['id']), forum['name'])
        if message:
            add_ctxtnav(context.req, topic['subject'],
              context.req.href.discussion(forum['id'], topic['id']),
              topic['subject'])

        # Add CSS styles and scripts.
        add_stylesheet(context.req, 'common/css/wiki.css')
        add_stylesheet(context.req, 'discussion/css/discussion.css')
        add_stylesheet(context.req, 'discussion/css/admin.css')
        add_script(context.req, 'common/js/trac.js')
        add_script(context.req, 'common/js/search.js')
        add_script(context.req, 'common/js/wikitoolbar.js')

        # Commit database changes and return template and data.
        db.commit()
        self.env.log.debug(self.data)
        return modes[-1] + '.html', {'discussion' : self.data}

    def _get_items(self, context):
        group, forum, topic, message = None, None, None, None

        # Populate active group.
        if context.req.args.has_key('group'):
            group_id = int(context.req.args.get('group') or 0)
            group = self.get_group(context, group_id)

        # Populate active forum.
        if context.req.args.has_key('forum'):
            forum_id = int(context.req.args.get('forum') or 0)
            forum = self.get_forum(context, forum_id)

        # Populate active topic.
        if context.req.args.has_key('topic'):
            topic_id = int(context.req.args.get('topic') or 0)
            topic = self.get_topic(context, topic_id)

        # Populate active topic.
        if context.req.args.has_key('message'):
            message_id = int(context.req.args.get('message') or 0)
            message = self.get_message(context, message_id)

        return group, forum, topic, message

    def _get_modes(self, context, group, forum, topic, message):
        # Get action.
        action = context.req.args.get('discussion_action')
        preview = context.req.args.has_key('preview');
        submit = context.req.args.has_key('submit');
        self.log.debug('realm: %s, action: %s, preview: %s, submit: %s' % (
          context.resource.realm, action, preview, submit))

        # Determine mode.
        if message:
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
                        return ['message-post-add', 'wiki-message-list']
                elif action == 'edit':
                    return ['message-edit', 'wiki-message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['wiki-message-list']
                    else:
                        return ['message-post-edit', 'wiki-message-list']
                elif action == 'delete':
                    return ['message-delete', 'wiki-message-list']
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
                        return ['message-post-add', 'wiki-message-list']
                elif action == 'edit':
                    return ['topic-edit', 'wiki-message-list']
                elif action == 'post-edit':
                    if preview:
                        return ['wiki-message-list']
                    else:
                        return ['topic-post-edit', 'wiki-message-list']
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
            if context.resource.realm == 'discussion-admin':
                if action == 'post-edit':
                    return ['forum-post-edit', 'admin-forum-list']
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
                        return ['topic-post-add', 'topic-list']
                elif action == 'delete':
                    return ['forum-delete', 'forum-list']
                else:
                    return ['topic-list']
        elif group:
            if context.resource.realm == 'discussion-admin':
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
            elif context.resource.realm == 'discussion-wiki':
                return ['wiki-message-list']
            else:
                if action == 'post-add':
                    return ['forum-post-add', 'forum-list']
                else:
                    return ['forum-list']
        else:
            if context.resource.realm == 'discussion-admin':
                if action == 'post-add':
                    return ['group-post-add', 'admin-group-list']
                elif action == 'delete':
                    return ['groups-delete', 'admin-group-list']
                else:
                    return ['admin-group-list']
            elif context.resource.realm == 'discussion-wiki':
                return ['wiki-message-list']
            else:
                if action == 'add':
                    return ['forum-add']
                elif action == 'post-add':
                    return ['forum-post-add', 'forum-list']
                else:
                    return ['forum-list']

    def _do_action(self, context, modes, group, forum, topic, message,
      is_moderator):
        for mode in modes:
            if mode == 'group-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Display groups.
                self.data['groups'] = self.get_groups(context)

            elif mode == 'admin-group-list':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')

                # Prepare values for edit form.
                if group:
                    self.data['name'] = group['name']
                    self.data['description'] = group['description']

                # Display groups.
                self.data['order'] = order
                self.data['desc'] = desc
                self.data['groups'] = self.get_groups(context, order, desc)

            elif mode == 'group-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

            elif mode == 'group-post-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                new_name = context.req.args.get('name')
                new_description = context.req.args.get('description')

                # Add new group.
                self.add_group(context, new_name, new_description)

                # Redirect request to prevent re-submit.
                context.req.redirect(context.req.href.discussion('redirect',
                  href = context.req.path_info))

            elif mode == 'group-post-edit':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                new_group = int(context.req.args.get('group') or 0)
                new_name = context.req.args.get('name')
                new_description = context.req.args.get('description')

                # Edit group.
                self.edit_group(context, new_group, new_name, new_description)

                # Redirect request to prevent re-submit.
                context.req.redirect(context.req.href.discussion('redirect',
                  href = context.req.path_info))

            elif mode == 'group-delete':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

            elif mode == 'groups-delete':
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
                context.req.redirect(context.req.href.discussion('redirect',
                  href = context.req.path_info))

            elif mode == 'forum-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Get form values.
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')

                # Display forums.
                self.data['order'] = order
                self.data['desc'] = desc
                self.data['groups'] = self.get_groups(context)
                self.data['forums'] = self.get_forums(context, order, desc)
                self.data['forum'] = None

            elif mode == 'admin-forum-list':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get ordering arguments values.
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')

                # Prepare values for edit form.
                if forum:
                    self.data['name'] = forum['name']
                    self.data['subject'] = forum['subject']
                    self.data['description'] = forum['description']
                    self.data['moderators'] = forum['moderators']
                    self.data['group'] = forum['group']

                # Display forums.
                self.data['order'] = order
                self.data['desc'] = desc
                self.data['users'] = self.get_users(context)
                self.data['groups'] = self.get_groups(context)
                self.data['forums'] = self.get_forums(context, order, desc)

            elif mode == 'forum-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Display Add Forum form.
                self.data['users'] = self.get_users(context)
                self.data['groups'] = self.get_groups(context)

            elif mode == 'forum-post-add':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values
                new_name = context.req.args.get('name')
                new_author = context.req.authname
                new_subject = context.req.args.get('subject')
                new_description = context.req.args.get('description')
                new_moderators = context.req.args.get('moderators')
                new_group = int(context.req.args.get('group') or 0)
                if not new_moderators:
                    new_moderators = []
                if not isinstance(new_moderators, list):
                     new_moderators = [new_moderators]

                # Perform new forum add.
                self.add_forum(context, new_name, new_author, new_subject,
                   new_description, new_moderators, new_group)

                # Redirect request to prevent re-submit.
                context.req.redirect(context.req.href.discussion('redirect',
                  href = context.req.path_info))

            elif mode == 'forum-post-edit':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Get form values.
                new_forum = int(context.req.args.get('forum') or 0)
                new_name = context.req.args.get('name')
                new_subject = context.req.args.get('subject')
                new_description = context.req.args.get('description')
                new_moderators = context.req.args.get('moderators')
                new_group = int(context.req.args.get('group') or 0)
                if not new_moderators:
                    new_moderators = []
                if not isinstance(new_moderators, list):
                    new_moderators = [new_moderators]

                # Perform forum edit.
                self.edit_forum(context, new_forum, new_name, new_subject,
                  new_description, new_moderators, new_group)

                # Redirect request to prevent re-submit.
                context.req.redirect(context.req.href.discussion('redirect',
                  href = context.req.path_info))

            elif mode == 'forum-delete':
                context.req.perm.assert_permission('DISCUSSION_ADMIN')

                # Delete forum.
                self.delete_forum(context, forum['id'])

                # Redirect request to prevent re-submit.
                context.req.redirect(context.req.href.discussion('redirect',
                  href = context.req.path_info))

            elif mode == 'forums-delete':
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
                context.req.redirect(context.req.href.discussion('redirect',
                  href = context.req.path_info))

            elif mode == 'topic-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Update this forum visit time.
                context.visited_forums[forum['id']] = to_timestamp(datetime.now(utc))

                # Get form values
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')

                # Display topics.
                self.data['order'] = order
                self.data['desc'] = desc
                self.data['topics'] = self.get_topics(context, forum['id'],
                  order, desc)

            elif mode == 'topic-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

                # Get form values.
                new_subject = context.req.args.get('subject')
                new_author = context.req.args.get('author')
                new_body = context.req.args.get('body')

                # Display Add Topic form.
                if new_subject:
                    self.data['subject'] = format_to_oneliner(self.env, context,
                      new_subject)
                if new_author:
                    self.data['author'] = format_to_oneliner(self.env, context,
                      new_author)
                if new_body:
                    self.data['body'] = format_to_html(self.env, context,
                      new_body)

            elif mode == 'topic-quote':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

                # Prepare old content.
                lines = topic['body'].splitlines()
                for I in xrange(len(lines)):
                    lines[I] = '> %s' % (lines[I])
                context.req.args['body'] = '\n'.join(lines)

                # Signalise that message is being added.
                context.req.args['message'] = message and  message['id'] or '-1'

            elif mode == 'topic-post-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

                # Get form values.
                new_subject = context.req.args.get('subject')
                new_author = context.req.args.get('author')
                new_body = context.req.args.get('body')
                new_time = to_timestamp(datetime.now(utc))

                self.log.debug((new_subject, new_body))

                # Add topic.
                self.add_topic(context, forum['id'], new_subject, new_time,
                  new_author, new_body)

                # Get new popic and notify about creation.
                new_topic = self.get_topic_by_time(context, new_time)
                to = self.get_topic_to_recipients(context, new_topic['id'])
                cc = self.get_topic_cc_recipients(context, new_topic['id'])
                notifier = DiscussionNotifyEmail(self.env)
                notifier.notify(context, mode, forum, new_topic, None, to, cc)

                # Redirect request to prevent re-submit.
                context.req.redirect(context.req.href.discussion('redirect',
                  href = context.req.path_info))

            elif mode == 'topic-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND')
                if not is_moderator and (topic['author'] !=
                  context.req.authname):
                    raise PermissionError('Topic edit')

                # Prepare form values.
                context.req.args['subject'] = topic['subject']
                context.req.args['body'] = topic['body']

            elif mode == 'topic-post-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND')
                if not is_moderator and (topic['author'] != 
                  context.req.authname):
                    raise PermissionError('Topic edit')

                # Get form values.
                new_subject = context.req.args.get('subject')
                new_body = context.req.args.get('body')
                self.log.debug('new_body: ' + new_body)

                # Edit topic.
                topic['subject'] = new_subject
                topic['body'] = new_body
                self.edit_topic(context, topic['id'], topic['forum'],
                  topic['subject'], topic['body'])

                # Redirect request to prevent re-submit.
                context.req.redirect(context.req.href.discussion('redirect',
                  href = context.req.path_info))

            elif mode == 'topic-move':
                context.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')

                # Display Move Topic form.
                self.data['forums'] = self.get_forums(context)

            elif mode == 'topic-post-move':
                context.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')

                # Get form values.
                new_forum = int(context.req.args.get('new_forum') or 0)

                # Move topic.
                self.set_forum(context, topic['id'], new_forum)

                # Redirect request to prevent re-submit.
                context.req.redirect(context.req.href.discussion('redirect',
                  href = context.req.path_info))

            elif mode == 'topic-delete':
                context.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')

                # Delete topic.
                self.delete_topic(context, topic['id'])

                # Redirect request to prevent re-submit.
                context.req.redirect(context.req.href.discussion('redirect',
                  href = context.req.path_info))

            elif mode == 'message-list':
                context.req.perm.assert_permission('DISCUSSION_VIEW')
                self._prepare_message_list(context, topic)

            elif mode == 'wiki-message-list':
                if topic:
                    self._prepare_message_list(context, topic)

            elif mode == 'message-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

                # Signalise that message is being added.
                context.req.args['message'] = message and  message['id'] or '-1'

            elif mode == 'message-quote':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

                # Prepare old content.
                lines = message['body'].splitlines()
                for I in xrange(len(lines)):
                    lines[I] = '> %s' % (lines[I])
                context.req.args['body'] = '\n'.join(lines)

            elif mode == 'message-post-add':
                context.req.perm.assert_permission('DISCUSSION_APPEND')

                # Get form values.
                new_author = context.req.args.get('author')
                new_body = context.req.args.get('body')
                new_time = to_timestamp(datetime.now(utc))

                # Add message.
                self.add_message(context, forum['id'], topic['id'], message and
                  message['id'] or '-1', new_time, new_author, new_body)

                # Get inserted message and notify about its creation.
                new_message = self.get_message_by_time(context, new_time)
                to = self.get_topic_to_recipients(context, topic['id'])
                cc = self.get_topic_cc_recipients(context, topic['id'])
                notifier = DiscussionNotifyEmail(self.env)
                notifier.notify(context, mode, forum, topic, new_message, to, cc)

                # Redirect request to prevent re-submit.
                if context.resource.realm != 'discussion-wiki':
                    context.req.redirect(context.req.href.discussion('redirect',
                      href = context.req.path_info))

            elif mode == 'message-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND')
                if not is_moderator and (message['author'] !=
                  context.req.authname):
                    raise PermissionError('Message edit')

                # Prepare form values.
                context.req.args['body'] = message['body']

            elif mode == 'message-post-edit':
                context.req.perm.assert_permission('DISCUSSION_APPEND')
                if not is_moderator and (message['author'] !=
                  context.req.authname):
                    raise PermissionError('Message edit')

                # Get form values.
                new_body = context.req.args.get('body')

                # Edit message.
                message['body'] = new_body
                self.edit_message(context, message['id'], message['forum'],
                  message['topic'], message['replyto'], new_body)

                # Redirect request to prevent re-submit.
                if context.resource.realm != 'discussion-wiki':
                    context.req.redirect(context.req.href.discussion('redirect',
                      href = context.req.path_info))

            elif mode == 'message-delete':
                context.req.perm.assert_permission('DISCUSSION_MODERATE')
                if not is_moderator:
                    raise PermissionError('Forum moderate')

                # Delete message.
                self.delete_message(context, message['id'])

                # Redirect request to prevent re-submit.
                if context.resource.realm != 'discussion-wiki':
                    context.req.redirect(context.req.href.discussion('redirect',
                      href = context.req.path_info))

            elif mode == 'message-set-display':
                context.req.perm.assert_permission('DISCUSSION_VIEW')

                # Get form values.
                display = context.req.args.get('display')

                # Set message list display mode to session.
                context.req.session['message-list-display'] = display

    def _prepare_message_list(self, context, topic):
        # Get form values.
        new_author = context.req.args.get('author')
        new_subject = context.req.args.get('subject')
        new_body = context.req.args.get('body')

        # Get time when topic was visited from session.
        visit_time = int(context.visited_topics.has_key(topic['id']) and
          (context.visited_topics[topic['id']] or 0))

        # Update this topic visit time.
        context.visited_topics[topic['id']] = to_timestamp(datetime.now(utc))

        # Mark new topic.
        if topic['time'] > visit_time:
            topic['new'] = True

        # Prepare display of topic.
        self.log.debug( (new_body,))
        if new_author != None:
            self.data['author'] = format_to_oneliner(self.env, context, new_author)
        if new_subject != None:
            self.data['subject'] = format_to_oneliner(self.env, context, new_subject)
        if new_body != None:
            self.data['body'] = format_to_html(self.env, context, new_body)

        # Prepare display of messages.
        display = context.req.session.get('message-list-display')
        self.data['display'] = display
        if display == 'flat-asc':
            self.data['messages'] = self.get_flat_messages(context,
              topic['id'], visit_time)
        elif display == 'flat-desc':
            self.data['messages'] = self.get_flat_messages(context,
              topic['id'], visit_time, 'ORDER BY time DESC')
        else:
            self.data['messages'] = self.get_messages(context, topic['id'],
              visit_time)

    # Get one item functions.

    def get_message(self, context, id):
        columns = ('id', 'forum', 'topic', 'replyto', 'time', 'author', 'body')
        sql = "SELECT id, forum, topic, replyto, time, author, body FROM" \
          " message WHERE id = %s"
        self.env.log.debug(sql % (to_unicode(id),))
        context.cursor.execute(sql, (to_unicode(id),))
        for row in context.cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_message_by_time(self, context, time):
        columns = ('id', 'forum', 'topic', 'replyto', 'time', 'author', 'body')
        sql = "SELECT id, forum, topic, replyto, time, author, body FROM" \
          " message WHERE time = %s"
        self.env.log.debug(sql % (time,))
        context.cursor.execute(sql, (time,))
        for row in context.cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_topic(self, context, id):
        columns = ('id', 'forum', 'subject', 'time', 'author', 'body')
        sql = "SELECT id, forum, subject, time, author, body FROM topic WHERE" \
          " id = %s"
        self.env.log.debug(sql % (to_unicode(id),))
        context.cursor.execute(sql, (to_unicode(id),))
        for row in context.cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_topic_by_time(self, context, time):
        columns = ('id', 'forum', 'subject', 'time', 'author', 'body')
        sql = "SELECT id, forum, subject, time, author, body FROM topic WHERE" \
          " time = %s"
        self.env.log.debug(sql % (time,))
        context.cursor.execute(sql, (time,))
        for row in context.cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_topic_by_subject(self, context, subject):
        columns = ('id', 'forum', 'subject', 'time', 'author', 'body')
        sql = "SELECT id, forum, subject, time, author, body FROM topic WHERE" \
          " subject = %s"
        self.env.log.debug(sql % (subject,))
        context.cursor.execute(sql, (subject,))
        for row in context.cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_topic_to_recipients(self, context, id):
        sql = "SELECT t.author FROM topic t WHERE t.id = %s UNION SELECT" \
          " m.author FROM message m WHERE m.topic = %s"
        self.env.log.debug(sql % (to_unicode(id), to_unicode(id)))
        context.cursor.execute(sql, (to_unicode(id), to_unicode(id)))
        to_recipients = []
        for row in context.cursor:
            to_recipients.append(row[0])
        return to_recipients

    def get_topic_cc_recipients(self, context, id):
        return []

    def get_forum(self, context, id):
        columns = ('id', 'group', 'name', 'subject', 'time', 'moderators',
          'description')
        sql = "SELECT id, forum_group, name, subject, time, moderators," \
           " description FROM forum WHERE id = %s"
        self.env.log.debug(sql % (to_unicode(id),))
        context.cursor.execute(sql, (to_unicode(id),))
        for row in context.cursor:
            row = dict(zip(columns, row))
            row['moderators'] = row['moderators'].split(' ')
            return row
        return None

    def get_group(self, context, id):
        columns = ('id', 'name', 'description')
        sql = "SELECT id, name, description FROM forum_group WHERE id = %s"
        self.env.log.debug(sql % (to_unicode(id),))
        context.cursor.execute(sql, (to_unicode(id),))
        for row in context.cursor:
            row = dict(zip(columns, row))
            return row
        return {'id' : 0, 'name': 'None', 'description': 'No Group'}

    # Get list functions.

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
            row['name'] = format_to_oneliner(self.env, context, row['name'])
            row['description'] = format_to_oneliner(self.env, context,
              row['description'])
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
        columns = ('id', 'name', 'author', 'time', 'moderators', 'group',
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
            row['moderators'] = format_to_oneliner(self.env, context,
              row['moderators'])
            row['subject'] = format_to_oneliner(self.env, context,
              row['subject'])
            row['description'] = format_to_oneliner(self.env, context,
              row['description'])
            row['lastreply'] = row['lastreply'] and pretty_timedelta(
              to_datetime(row['lastreply'], utc)) or 'No replies'
            row['lasttopic'] = row['lasttopic'] and  pretty_timedelta(
              to_datetime(row['lasttopic'], utc)) or 'No topics'
            row['topics'] = row['topics'] or 0
            row['replies'] = row['replies'] and int(row['replies']) or 0
            row['time'] = format_datetime(row['time'])
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
            row['author'] = format_to_oneliner(self.env, context, row['author'])
            row['subject'] = format_to_oneliner(self.env, context, row['subject'])
            row['body'] = format_to_html(self.env, context, row['body'])
            row['lastreply'] = row['lastreply'] and pretty_timedelta(
              to_datetime(row['lastreply'], utc)) or 'No replies'
            row['replies'] = row['replies'] or 0
            row['time'] = format_datetime(row['time'])
            topics.append(row)

        # Compute count of new replies.
        for topic in topics:
            topic['new_replies'] = _get_new_replies_count(context, topic['id'])

        return topics

    def get_messages(self, context, topic_id, time, order_by = 'time', desc = False):
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
            row['author'] = format_to_oneliner(self.env, context, row['author'])
            row['body'] = format_to_html(self.env, context, row['body'])
            if int(row['time']) > time:
                row['new'] = True
            row['time'] = format_datetime(row['time'])
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

    def get_flat_messages(self, context, topic_id, time, order_by =
      'ORDER BY time ASC'):
        columns = ('id', 'replyto', 'time', 'author', 'body')
        sql = "SELECT m.id, m.replyto, m.time, m.author, m.body FROM message m" \
          " WHERE m.topic = %s " + order_by
        self.env.log.debug(sql % (to_unicode(topic_id),))
        context.cursor.execute(sql, (to_unicode(topic_id),))
        messages = []
        for row in context.cursor:
            row = dict(zip(columns, row))
            row['author'] = format_to_oneliner(self.env, context, row['author'])
            row['body'] = format_to_html(self.env, context, row['body'])
            if int(row['time']) > time:
                row['new'] = True
            row['time'] = format_datetime(row['time'])
            messages.append(row)
        return messages

    def get_users(self, context):
        users = []
        for user in self.env.get_known_users():
            users.append(user[0])
        return users

    # Add items functions.

    def add_group(self, context, name, description):
        sql = "INSERT INTO forum_group (name, description) VALUES (%s, %s)"
        self.env.log.debug(sql % (name, description))
        context.cursor.execute(sql, (name, description))

    def add_forum(self, context, name, author, subject, description, moderators,
      group):
        moderators = ' '.join(moderators)
        sql = "INSERT INTO forum (name, author, time, moderators, subject," \
          " description, forum_group) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        self.env.log.debug(sql % (name, author, to_timestamp(datetime.now(utc)),
          moderators, subject, description, group))
        context.cursor.execute(sql, (name, author, to_timestamp(datetime.now(utc)),
          moderators, subject, description, group))

    def add_topic(self, context, forum, subject, time, author, body):
        sql = "INSERT INTO topic (forum, subject, time, author, body) VALUES" \
          " (%s, %s, %s, %s, %s)"
        self.env.log.debug(sql % (forum, subject, time, author, body))
        context.cursor.execute(sql, (forum, subject, time, author, body))

    def add_message(self, context, forum, topic, replyto, time, author, body):
        sql = "INSERT INTO message (forum, topic, replyto, time, author," \
          " body) VALUES (%s, %s, %s, %s, %s, %s)"
        self.env.log.debug(sql % (forum, topic, replyto, time, author, body))
        context.cursor.execute(sql, (forum, topic, replyto, time, author, body))

    # Delete items functions.

    def delete_group(self, context, group):
        sql = "DELETE FROM forum_group WHERE id = %s"
        self.env.log.debug(sql % (to_unicode(group),))
        context.cursor.execute(sql, (to_unicode(group),))
        sql = "UPDATE forum SET forum_group = 0 WHERE forum_group = %s"
        self.env.log.debug(sql % (to_unicode(group),))
        context.cursor.execute(sql, (to_unicode(group),))

    def delete_forum(self, context, forum):
        sql = "DELETE FROM message WHERE forum = %s"
        self.env.log.debug(sql % (to_unicode(forum),))
        context.cursor.execute(sql, (to_unicode(forum),))
        sql = "DELETE FROM topic WHERE forum = %s"
        self.env.log.debug(sql % (to_unicode(forum),))
        context.cursor.execute(sql, (to_unicode(forum),))
        sql = "DELETE FROM forum WHERE id = %s"
        self.env.log.debug(sql % (to_unicode(forum),))
        context.cursor.execute(sql, (to_unicode(forum),))

    def delete_topic(self, context, topic):
        sql = "DELETE FROM message WHERE topic = %s"
        self.env.log.debug(sql % (to_unicode(topic),))
        context.cursor.execute(sql, (to_unicode(topic),))
        sql = "DELETE FROM topic WHERE id = %s"
        self.env.log.debug(sql % (to_unicode(topic),))
        context.cursor.execute(sql, (to_unicode(topic),))

    def delete_message(self, context, message):
        # Get message replies.
        sql = "SELECT m.id FROM message m WHERE m.replyto = %s"
        self.env.log.debug(sql % (to_unicode(message),))
        context.cursor.execute(sql, (to_unicode(message),))
        replies = []

        # Get all replies first.
        for row in context.cursor:
            replies.append(row[0])

        # Delete all replies.
        for reply in replies:
            self.delete_message(context, reply)

        # Delete message itself.
        sql = "DELETE FROM message WHERE id = %s"
        self.env.log.debug(sql % (to_unicode(message),))
        context.cursor.execute(sql, (to_unicode(message),))

    # Set item functions.

    def set_group(self, context, forum, group):
        if not group:
            group = '0'
        sql = "UPDATE forum SET forum_group = %s WHERE id = %s"
        self.env.log.debug(sql % (group, forum))
        context.cursor.execute(sql, (group, forum))

    def set_forum(self, context, topic, forum):
        sql = "UPDATE topic SET forum = %s WHERE id = %s"
        self.env.log.debug(sql % (forum, topic))
        context.cursor.execute(sql, (forum, topic))
        sql = "UPDATE message SET forum = %s WHERE topic = %s"
        self.env.log.debug(sql % (forum, topic))
        context.cursor.execute(sql, (forum, topic))

    # Edit functions.

    def edit_group(self, context, group, name, description):
        sql = "UPDATE forum_group SET name = %s, description = %s WHERE id = %s"
        self.env.log.debug(sql % (name, description, group))
        context.cursor.execute(sql, (name, description, group))

    def edit_forum(self, context, forum, name, subject, description, moderators,
      group):
        moderators = ' '.join(moderators)
        if not group:
            group = '0'
        sql = "UPDATE forum SET name = %s, subject = %s, description = %s," \
          " moderators = %s, forum_group = %s WHERE id = %s"
        self.env.log.debug(sql % (name, subject, description, moderators,
          group, forum))
        context.cursor.execute(sql, (name, subject, description, moderators,
          group, forum))

    def edit_topic(self, context, topic, forum, subject, body):
        sql = "UPDATE topic SET forum = %s, subject = %s, body = %s WHERE id" \
          " = %s"
        self.env.log.debug(sql % (forum, subject, body, topic))
        context.cursor.execute(sql, (forum, subject, body, topic))

    def edit_message(self, context, message, forum, topic, replyto, body):
        sql = "UPDATE message SET forum = %s, topic = %s, replyto = %s, body" \
          " = %s WHERE id = %s"
        self.env.log.debug(sql % (forum, topic, replyto, body, message))
        context.cursor.execute(sql, (forum, topic, replyto, body, message))
