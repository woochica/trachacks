# -*- coding: utf-8 -*-
from trac.core import *
from trac.config import BoolOption
from trac.wiki.api import IWikiChangeListener
from announcerplugin.api import AnnouncementSystem, AnnouncementEvent
from tracfullblog.api import IBlogChangeListener
from tracfullblog.core import FullBlogCore
from tracfullblog.model import BlogPost, BlogComment

class BlogChangeEvent(AnnouncementEvent):
    def __init__(self, blog_post, category, url, blog_comment=None):
        AnnouncementEvent.__init__(self, 'blog', category, blog_post)
        if blog_comment:
            if 'comment deleted' == category:
                self.comment = blog_comment['comment']
                self.author = blog_comment['author']
                self.timestamp = blog_comment['time']
            else:
                self.comment = blog_comment.comment
                self.author = blog_comment.author
                self.timestamp = blog_comment.time
        else:
            self.comment = blog_post.version_comment
            self.author = blog_post.version_author
            self.timestamp = blog_post.version_time
        self.remote_addr = url 
        self.version = blog_post.version
        self.blog_post = blog_post
        self.blog_comment = blog_comment

class BlogChangeProducer(Component):
    implements(IBlogChangeListener)
    
    def blog_post_changed(self, postname, version):
        """Called when a new blog post 'postname' with 'version' is added .
        version==1 denotes a new post, version>1 is a new version on existing 
        post."""
        blog_post = BlogPost(self.env, postname, version)
        action = 'post created'
        if version > 1:
            action = 'post changed' 
        announcer = AnnouncementSystem(self.env)
        announcer.send(
            BlogChangeEvent(
                blog_post, 
                action, 
                self.env.abs_href.blog(blog_post.name)
            )
        )

    def blog_post_deleted(self, postname, version, fields):
        """Called when a blog post is deleted:
        version==0 means all versions (or last remaining) version is deleted.
        Any version>0 denotes a specific version only.
        Fields is a dict with the pre-existing values of the blog post.
        If all (or last) the dict will contain the 'current' version 
        contents."""
        blog_post = BlogPost(self.env, postname, version)
        announcer = AnnouncementSystem(self.env)
        announcer.send(
            BlogChangeEvent(
                blog_post, 
                'post deleted', 
                self.env.abs_href.blog(blog_post.name)
            )
        )

    def blog_comment_added(self, postname, number):
        """Called when Blog comment number N on post 'postname' is added."""
        blog_post = BlogPost(self.env, postname, 0)
        blog_comment = BlogComment(self.env, postname, number)
        announcer = AnnouncementSystem(self.env)
        announcer.send(
            BlogChangeEvent(
                blog_post, 
                'comment created', 
                self.env.abs_href.blog(blog_post.name),
                blog_comment
            )
        )

    def blog_comment_deleted(self, postname, number, fields):
        """Called when blog post comment 'number' is deleted.
        number==0 denotes all comments is deleted and fields will be empty.
            (usually follows a delete of the blog post).
        number>0 denotes a specific comment is deleted, and fields will contain
            the values of the fields as they existed pre-delete."""
        blog_post = BlogPost(self.env, postname, 0)
        announcer = AnnouncementSystem(self.env)
        announcer.send(
            BlogChangeEvent(
                blog_post, 
                'comment deleted', 
                self.env.abs_href.blog(blog_post.name),
                fields
            )
        )

