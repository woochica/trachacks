# -*- coding: utf-8 -*-

from announcerplugin.api import IAnnouncementFormatter
from genshi.template import NewTextTemplate
from genshi.template import TemplateLoader
from trac.config import Option
from trac.core import *
from trac.web.chrome import Chrome

class BlogEmailFormatter(Component):
    implements(IAnnouncementFormatter)

    blog_email_subject = Option('fullblog-announcement', 'blog_email_subject',
            "Blog: ${blog.name} ${action}",
            """Format string for the blog email subject.  This is a
            mini genshi template and it is passed the blog_post and action
            objects.""")

    def get_format_transport(self):
        return 'email'

    def get_format_realms(self, transport):
        if transport == 'email':
            yield 'blog'

    def get_format_styles(self, transport, realm):
        if transport == 'email' and realm == 'blog':
            yield 'text/plain'

    def get_format_alternative(self, transport, realm, style):
        if transport == 'email' and realm == 'blog':
            yield 'text/plain'

    def format(self, transport, realm, style, event):
        if transport == 'email' and realm == 'blog' and style == 'text/plain':
            blog_post = event.blog_post
            blog_comment = event.blog_comment
            data = dict(
                name = blog_post.name,
                author = event.author,
                time = event.timestamp,
                category = event.category,
                version = event.version,
                link = event.remote_addr,
                title = blog_post.title,
                body = blog_post.body,
                comment = event.comment,
            )
            chrome = Chrome(self.env)
            dirs = []
            for provider in chrome.template_providers:
                dirs += provider.get_templates_dirs()
            templates = TemplateLoader(dirs, variable_lookup='lenient')
            template = templates.load(
                'fullblogannouncement_email_plaintext.txt',
                cls=NewTextTemplate
            )
            if template:
                stream = template.generate(**data)
                output = stream.render('text')
            return output

    def format_subject(self, transport, realm, style, event):
        if transport is 'email' and realm is 'wiki' and style is 'test/plain':
            template = NewTextTemplate(self.blog_email_subject)
            return template.generate(
                blog=event.blog_post, 
                action=event.category
            ).render()

    def format_headers(self, transport, realm, style, event):
        return {}
