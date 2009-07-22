# -*- coding: utf-8 -*-

from datetime import datetime

from trac.core import *
from trac.resource import Resource
from trac.web.chrome import Chrome
from trac.notification import NotifyEmail
from trac.util import md5, format_datetime
from trac.util.datefmt import to_timestamp
from trac.util.text import to_unicode

from trac.web.chrome import ITemplateProvider

from genshi.template import TemplateLoader, TextTemplate

from tracdiscussion.api import *

class DiscussionNotifyEmail(NotifyEmail):

    template_name = 'discussion-notify-body.txt'
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
        elif self.topic:
            self.topic['link'] = self.env.abs_href.discussion('topic',
              self.topic['id'])

        # Send e-mail to all subscribers.
        self.to_recipients = forum['subscribers'] + topic['subscribers']

        # Render subject template and send notification.
        subject = (to_unicode(Chrome(self.env).render_template(context.req,
          'discussion-notify-subject.txt', self.data, 'text/plain'))).strip()
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
        else:
            # Should not happen.
            raise TracError('DiscussionPlugin internal error.')

        # Send e-mail.
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

class DiscussionEmailNotification(Component):
    """
        The e-mail notification component implements topic and message change
        listener interfaces and send e-mail notifications when topics and
        messages are created.
    """
    implements(ITopicChangeListener, IMessageChangeListener)

    # ITopicChangeListener methods.

    def topic_created(self, context, topic):
        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Get access to api component.
        api = self.env[DiscussionApi]
        forum = api.get_forum(context, topic['forum'])

        # Send e-mail notification.
        notifier = DiscussionNotifyEmail(self.env)
        notifier.notify(context, forum, topic, None)

    def topic_changed(self, context, topic, old_topic):
        pass

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
