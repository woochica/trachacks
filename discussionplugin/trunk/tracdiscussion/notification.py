# -*- coding: utf-8 -*-

from trac.core import *
from trac.web.chrome import Chrome
from trac.notification import NotifyEmail
from trac.util import format_datetime
from trac.util.text import to_unicode

from trac.web.chrome import ITemplateProvider

from genshi.template import TemplateLoader, TextTemplate

class DiscussionNotifyEmail(NotifyEmail):

    template_name = 'discussion-notify-body.txt'
    forum = None
    topic = None
    message = None
    torcpts = []
    ccrcpts = []
    from_email = 'trac+discussion@localhost'
    COLS = 75

    def __init__(self, env):
        NotifyEmail.__init__(self, env)

    def notify(self, context, action, forum = None, topic = None,
      message = None, torcpts = [], ccrcpts = []):
        # Init internal data structure.
        self.data = {}

        # Store link to currently notifying forum, topic and message.
        self.forum = forum
        self.topic = topic
        self.message = message
        self.torcpts = torcpts
        self.ccrcpts = ccrcpts

        # Get action and item of action.
        item, sep, action = action.split('-')

        # Which item notify about:
        if item == 'topic':
            # Prepare topic specific fields.
            re = ''
            title = 'Topic'
            id = self.topic['id']
            author = "    Author:  %s" % self.topic['author']
            time = "      Time:  %s" % format_datetime(self.topic['time'])
            body = self.topic['body']
            link = self.env.abs_href.discussion('topic', self.topic['id'])

            # Save link for bad times.
            topic['link'] = link
        elif item == 'message':
            # Prepare message specific fields
            re = 'Re: '
            title = 'Message'
            id = self.message['id']
            author = "    Author:  %s" % self.message['author']
            time = "      Time:  %s" % format_datetime(self.message['time'])
            body = self.message['body']
            link = self.env.abs_href.discussion('message',self.message['id'])  \
              + '#%s' % self.message['id']

            # Save link for bad times.
            message['link'] = link
        else:
            return

        prefix = self.config.get('notification', 'smtp_subject_prefix')
        if prefix == '__default__':
            prefix = self.env.project_name
        moderators = "Moderators:  %s" % ' '.join(self.forum['moderators'])
        subject = self.topic['subject']

        # Set set e-mail template values.
        self.data.update({'discussion' : {'re' : re, 'prefix': prefix, 'title' : title, 'id' :
          id, 'author' : author, 'time' : time, 'moderators' : moderators,
          'subject' : subject, 'body' : body, 'link' : link}})

        # Render subject template and send notification.
        subject = to_unicode(Chrome(self.env).render_template(context.req,
          'discussion-notify-subject.txt', self.data, 'text/plain'))
        NotifyEmail.notify(self, id, subject)

    def get_message_id(self, forum_id, topic_id, message_id):
        # Fix ID of messages replying to topic.
        if message_id < 0:
            message_id = 0

        # Construct Message-ID according to RFC 2822.
        id = '%s.%s.%s' % (forum_id, topic_id, message_id)
        host = self.from_email[self.from_email.find('@') + 1:]
        return '<%s@%s>' % (id, host)

    def get_recipients(self, resid):
        return (self.torcpts, self.ccrcpts)

    def send(self, torcpts, ccrcpts):
        header = {}

        # Add item specific e-mail header fields.
        if self.message:
            # Get this messge ID.
            header['Message-ID'] = self.get_message_id(self.forum['id'],
              self.topic['id'], self.message['id'])
            header['X-Trac-Message-ID'] = to_unicode(self.message['id'])
            header['X-Trac-Discussion-URL'] = self.message['link']

            # Get replied message ID.
            reply_id = self.get_message_id(self.forum['id'], self.topic['id'],
              self.message['replyto'])
            header['In-Reply-To'] = reply_id
            header['References'] = reply_id
        else:
            # Get this message ID.
            header['Message-ID'] = self.get_message_id(self.forum['id'],
              self.topic['id'], 0)
            header['X-Trac-Topic-ID'] = to_unicode(self.topic['id'])
            header['X-Trac-Discussion-URL'] = self.topic['link']

        # Send e-mail.
        self.log.debug("Sending notification e-mail to %s and %s." % (torcpts,
          ccrcpts))
        NotifyEmail.send(self, torcpts, ccrcpts, header)
