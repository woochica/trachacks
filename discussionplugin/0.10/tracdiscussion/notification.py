# -*- coding: utf8 -*-

from trac.notification import NotifyEmail
from trac.util import format_datetime
from trac.util.text import CRLF, wrap

class DiscussionNotifyEmail(NotifyEmail):

    template_name = "discussion-notify-body.cs"
    COLS = 75

    def __init__(self, env):
        NotifyEmail.__init__(self, env)

    def notify(self, req, cursor, action, object):
        self.env.log.debug("action: %s" % action)
        self.env.log.debug("object: %s" % object)

        # Prepare action specific email content.
        if action == 'topic-post-add':
            title = 'Topic'
            re = ''
            link = req.abs_href.discussion(object['forum'], object['id'])
        elif action == 'topic-post-edit':
            title = 'Topic'
            re = ''
            link = req.abs_href.discussion(object['forum'], object['id'])
        elif action == 'message-post-add':
            title = 'Message'
            re = 'Re: '
            link = req.abs_href.discussion(object['forum'], object['topic'],
              object['id']) + '#%s' % object['id']
        elif action == 'message-post-edit':
            title = 'Message'
            re = 'Re: '
            link = req.abs_href.discussion(object['forum'], object['topic'],
              object['id']) + '#%s' % object['id']

        # Format body table items.
        author = "    Author:  %s" % object['author']
        time = "      Time:  %s" % format_datetime(object['time'])
        moderators = "Moderators: %s" % object['moderators']

        # Set set e-mail template values.
        self.hdf.set_unescaped('discussion.re', re)
        prefix = self.config.get('notification', 'smtp_subject_prefix')
        if prefix != '__default__':
            self.hdf.set_unescaped('discussion.prefix', prefix)
        self.hdf.set_unescaped('discussion.title', title)
        self.hdf.set_unescaped('discussion.id', object['id'])
        self.hdf.set_unescaped('discussion.author', author)
        self.hdf.set_unescaped('discussion.moderators', moderators)
        self.hdf.set_unescaped('discussion.time', time)
        self.hdf.set_unescaped('discussion.subject', object['subject'])
        self.hdf.set_unescaped('discussion.body', object['body'])
        self.hdf.set_unescaped('discussion.link', link)

        # Render body and send notification.
        subject = self.hdf.render('discussion-notify-subject.cs')
        self.env.log.debug(subject)
        NotifyEmail.notify(self, object['id'], subject)

    def get_recipients(self, resid):
        return ([], [])
