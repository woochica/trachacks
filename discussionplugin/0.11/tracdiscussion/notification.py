# -*- coding: utf-8 -*-

# Standard imports.
from datetime import datetime

# Trac imports.
from trac.core import *
from trac.config import ListOption
from trac.resource import Resource
from trac.web.chrome import Chrome
from trac.notification import NotifyEmail
from trac.util import md5, format_datetime
from trac.util.datefmt import to_timestamp
from trac.util.text import to_unicode
from trac.util.translation import _

# Trac interfaces.
from trac.web.chrome import ITemplateProvider

# Genshi imports.
from genshi.template import TemplateLoader, TextTemplate

# Local imports.
from tracdiscussion.api import *

class DiscussionNotifyEmail(NotifyEmail):

    template_name = 'topic-notify-body.txt'
    forum = None
    topic = None
    message = None
    from_email = 'trac+discussion@localhost'
    to_recipients = []
    cc_recipients = []
    COLS = 75

    def __init__(self, env):
        NotifyEmail.__init__(self, env)
        self.prev_cc = []

    def notify(self, context, forum = None, topic = None, message = None):
        # Store link to currently notifying forum, topic and message.
        self.forum = forum
        self.topic = topic
        self.message = message

        # Initialize template data.
        data = {}
        data['forum'] = self.forum
        data['topic'] = self.topic
        data['message'] = self.message
        data['prefix'] = self.config.get('notification', 'smtp_subject_prefix')
        if data['prefix'] == '__default__':
            data['prefix'] = self.env.project_name
        self.data.update({'discussion' : data})

        # Which item notify about?
        if self.message:
            self.message['link'] = self.env.abs_href.discussion('message',
              self.message['id'])
            self.template_name = 'message-notify-body.txt'
        elif self.topic:
            self.topic['link'] = self.env.abs_href.discussion('topic',
              self.topic['id'])
            self.template_name = 'topic-notify-body.txt'

        # Send e-mail to all subscribers.
        self.cc_recipients = forum['subscribers'] + topic['subscribers'] + \
          self.config.getlist('discussion', 'smtp_always_cc')

        # Render subject template and send notification.
        subject = (to_unicode(Chrome(self.env).render_template(context.req,
          self.message and 'message-notify-subject.txt' or
          'topic-notify-subject.txt', self.data, 'text/plain'))).strip()
        NotifyEmail.notify(self, id, subject)

    def invite(self, context, forum = None, topic = None, recipients = []):
        # Store link to currently notifying forum.
        self.forum = forum
        self.topic = topic

        # Initialize template data.
        data = {}
        data['forum'] = self.forum
        data['topic'] = self.topic
        data['prefix'] = self.config.get('notification', 'smtp_subject_prefix')
        if data['prefix'] == '__default__':
            data['prefix'] = self.env.project_name
        self.data.update({'discussion' : data})

        # Which item notify about?
        if self.topic:
            self.topic['link'] = self.env.abs_href.discussion('topic',
              self.topic['id'])
            self.template_name = 'topic-invite-body.txt'
        elif self.forum:
            self.forum['link'] = self.env.abs_href.discussion('forum',
              self.forum['id'])
            self.template_name = 'forum-invite-body.txt'

        # Send e-mail to all subscribers.
        self.cc_recipients = recipients + self.config.getlist('discussion',
          'smtp_always_cc')

        # Render subject template and send notification.
        subject = (to_unicode(Chrome(self.env).render_template(context.req,
          self.topic and 'topic-invite-subject.txt' or
            'forum-invite-subject.txt', self.data, 'text/plain'))).strip()
        NotifyEmail.notify(self, id, subject)

    def send(self, to_recipients, cc_recipients):
        header = {}

        # Add item specific e-mail header fields.
        if self.message:
            # ID of the message.
            header['Message-ID'] = self.get_message_email_id(self.message['id'])
            header['X-Trac-Message-ID'] = to_unicode(self.message['id'])
            header['X-Trac-Discussion-URL'] = self.message['link']

            # ID of replied message.
            if self.message['replyto'] != -1:
                reply_id = self.get_message_email_id(self.message['replyto'])
            else:
                reply_id = self.get_topic_email_id(self.message['topic'])
            header['In-Reply-To'] = reply_id
            header['References'] = reply_id
        elif self.topic:
            # ID of the message.
            header['Message-ID'] = self.get_topic_email_id(self.topic['id'])
            header['X-Trac-Topic-ID'] = to_unicode(self.topic['id'])
            header['X-Trac-Discussion-URL'] = self.topic['link']
        elif self.forum:
            # ID of the message.
            header['Message-ID'] = self.get_forum_email_id(self.forum['id'])
            header['X-Trac-Forum-ID'] = to_unicode(self.forum['id'])
            header['X-Trac-Discussion-URL'] = self.forum['link']
        else:
            # Should not happen.
            raise TracError('DiscussionPlugin internal error.')

        # Send e-mail.
        self.template = Chrome(self.env).load_template(self.template_name,
          method = 'text')
        self.env.log.debug('to_recipients: %s cc_recipients: %s' % (
          to_recipients, cc_recipients))
        NotifyEmail.send(self, to_recipients, cc_recipients, header)

    def get_recipients(self, item_id):
        return (self.to_recipients, self.cc_recipients)

    def get_message_email_id(self, message_id):
        # Generate a predictable, but sufficiently unique message ID.
        s = 'm.%s.%08d' % (self.config.get('project', 'url'), int(message_id))
        digest = md5(s).hexdigest()
        host = self.from_email[self.from_email.find('@') + 1:]
        email_id = '<%03d.%s@%s>' % (len(s), digest, host)
        return email_id

    def get_topic_email_id(self, topic_id):
        # Generate a predictable, but sufficiently unique topic ID.
        s = 't.%s.%08d' % (self.config.get('project', 'url'), int(topic_id))
        digest = md5(s).hexdigest()
        host = self.from_email[self.from_email.find('@') + 1:]
        email_id = '<%03d.%s@%s>' % (len(s), digest, host)
        return email_id

    def get_forum_email_id(self, forum_id):
        # Generate a predictable, but sufficiently unique topic ID.
        s = 'f.%s.%08d' % (self.config.get('project', 'url'), int(forum_id))
        digest = md5(s).hexdigest()
        host = self.from_email[self.from_email.find('@') + 1:]
        email_id = '<%03d.%s@%s>' % (len(s), digest, host)
        return email_id

class DiscussionEmailNotification(Component):
    """
        The e-mail notification component implements topic and message change
        listener interfaces and send e-mail notifications when topics and
        messages are created.
    """
    implements(IForumChangeListener, ITopicChangeListener,
      IMessageChangeListener)

    # Configuration options.

    smtp_always_cc = ListOption('discussion', 'smtp_always_cc', [],
        doc=_('''Always send discussion notifications to the listed e-mail
                 addresses.'''))

    # IForumChangeListener methods.

    def forum_created(self, context, forum):
        # Send e-mail invitation.
        notifier = DiscussionNotifyEmail(self.env)
        notifier.invite(context, forum, None, forum['subscribers'])

    def forum_changed(self, context, forum, old_forum):
        # Get new subscribers to topic.
        new_subscribers = [subscriber for subscriber in forum['subscribers']
          if subscriber not in old_forum['subscribers']]

        # We need to use complete forum dictionary.
        old_forum.update(forum)

        # Send e-mail invitation.
        notifier = DiscussionNotifyEmail(self.env)
        notifier.invite(context, old_forum, None, new_subscribers)

    def forum_deleted(self, context, forum):
        self.log.debug('DiscussionEmailNotification.forum_deleted()')

    # ITopicChangeListener methods.

    def topic_created(self, context, topic):
        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Get forum of the topic.
        api = self.env[DiscussionApi]
        forum = api.get_forum(context, topic['forum'])

        # Send e-mail notification.
        notifier = DiscussionNotifyEmail(self.env)
        notifier.notify(context, forum, topic, None)

    def topic_changed(self, context, topic, old_topic):
        if topic.has_key('subscribers'):
            # Get new subscribers to topic.
            new_subscribers = [subscriber for subscriber in topic['subscribers']
              if subscriber not in old_topic['subscribers']]

            # We need to use complete topic dictionary.
            old_topic.update(topic)

            # Get database access.
            db = self.env.get_db_cnx()
            context.cursor = db.cursor()

            # Get forum of the topic.
            api = self.env[DiscussionApi]
            forum = api.get_forum(context, old_topic['forum'])

            # Send e-mail invitation.
            notifier = DiscussionNotifyEmail(self.env)
            notifier.invite(context, forum, old_topic, new_subscribers)

    def topic_deleted(self, context, topic):
        pass

    # IMessageChangeListener methods.

    def message_created(self, context, message):
        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Get access to api component.
        api = self.env[DiscussionApi]
        forum = api.get_forum(context, message['forum'])
        topic = api.get_topic(context, message['topic'])

        # Send e-mail notification.
        notifier = DiscussionNotifyEmail(self.env)
        notifier.notify(context, forum, topic, message)

    def message_changed(self, context, message, old_message):
        pass

    def message_deleted(self, context, message):
        pass
