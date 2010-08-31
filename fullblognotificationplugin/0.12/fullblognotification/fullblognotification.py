# -*- coding: utf-8 -*-
"""
Notification of blog post/comment changes

Copyright Nick Loeve 2008
"""

import datetime

from notification import FullBlogNotificationEmail
from tracfullblog.api import IBlogChangeListener
from tracfullblog.model import BlogPost, BlogComment

from trac.config import Option, ListOption, BoolOption
from trac.core import *
from trac.util.datefmt import utc
from trac.web.chrome import ITemplateProvider

class FullBlogNotificationPlugin(Component):
    
    implements(ITemplateProvider, IBlogChangeListener)

    always_notify_author = BoolOption(
        'fullblog-notification', 'always_notify_author', 'false',
        """If true, Always notify the author of a blog change. 
           Defaults to false.""")

    from_email = Option(
        'fullblog-notification', 'from_email', 'trac+blog@localhost',
        """Sender address to use in notification emails.""")

    from_name = Option(
        'fullblog-notification', 'from_name', None,
        """Sender name to use in notification emails.
           Defaults to project name.""")

    notification_actions = ListOption(
        'fullblog-notification', 'notification_actions',
        'post_created, post_updated, post_comment_added, post_deleted',
        doc="""Actions for which notification emails are sent. Defaults to 'all'
        """)

    smtp_always_cc = ListOption(
        'fullblog-notification', 'smtp_always_cc', [],
        doc="""Comma separated list of email address(es) to always send
        notifications to. Addresses can be seen by all recipients (Cc:).""")

    subject_template = Option(
        'fullblog-notification', 'subject_template',
        '$prefix $blog.title $action',
        "Genshi text template snippet used for the notification subject.")

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []

    # IBlogChangeListener methods
    def blog_post_changed(self, postname, version):
        action = 'post_created'        
        blog_post = BlogPost(self.env, postname, version)
        notifier = FullBlogNotificationEmail(self.env)
        if version > 1:
            action = 'post_updated' 
        notifier.notify(blog_post, action, version, blog_post.version_time, blog_post.version_comment, blog_post.version_author)

    def blog_post_deleted(self, postname, version, fields):
        action = 'post_deleted'
        blog_post = BlogPost(self.env, postname, version)
        # the post has already been deleted, so populate from fields
        # this is just so we can say which page was deleted
        blog_post.title = fields['title']
        notifier = FullBlogNotificationEmail(self.env)
        author = fields['author']
        time = datetime.datetime.now(utc)
        if version > 0:
            action = 'post_deleted_version'
            author = fields['version_author']            
        notifier.notify(blog_post, action, version, time, '', author)

    def blog_comment_added(self, postname, number):
        action = 'post_comment_added'
        blog_post = BlogPost(self.env, postname, 0)
        bc = BlogComment(self.env, postname, number)
        notifier = FullBlogNotificationEmail(self.env)
        notifier.notify(blog_post, action, blog_post.version, bc.time, bc.comment, bc.author)

    def blog_comment_deleted(self, postname, number, fields):
        pass # nothing for now
