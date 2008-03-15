# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at:
# http://trac-hacks.org/wiki/TracBlogPlugin
#
# Author: John Hampton <pacopablo@pacopablo.com>
import os
import os.path
import time
import inspect
import re
import urlparse
from pkg_resources import resource_filename

from genshi.builder import tag

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.perm import IPermissionRequestor
from trac.util import Markup
from trac.wiki.formatter import wiki_to_html
from trac.wiki.model import WikiPage
from trac.wiki.macros import WikiMacroBase
from trac.config import Option, ListOption, BoolOption
from trac.resource import *

from tracblog.parseargs import parseargs

from tractags.api import TagSystem


__all__ = ['BlogPost']

_tag_split = re.compile('[,\s]+')

ENTRY_BASE = '/blog/new'

class BlogPost(WikiMacroBase):
    """Inserts a link to create a new blog post

    Accepts keyword arguments that specify default parameters.  The macro will
    be hidden unless the user has {{{BLOG_POSTER}}} permissions.

    '''tag''' - Tag that populates the "Tag under" field.  This key may be 
    specified as a tuple or list to pass multiple values.[[br]]
    '''blogtitle''' - Default blog entry title.[[br]]
    '''text''' - Default entry body text.[[br]]
    '''page_format''' - Default wiki page name.[[br]]
    '''readonly''' - Default readonly page status.[[br]]
    '''link''' - Text to display as the link.[[br]]

    === Examples ===
    {{{
    [[BlogPost()]]
    [[BlogPost(tag=(blog,pacopablo))]]
    [[BlogPost(tag=blog,blogtitle="A Simple Title",text="Body Text")]]
    [[BlogPost(tag=blog,pagename=blog/newpage,readonly=1)]]
    [[BlogPost(tag=(blog,pacopablo),link="A New Blog Post")]]
    }}}
    """

    implements(IRequestHandler, ITemplateProvider, IPermissionRequestor)

    page_format = Option('blog', 'page_format', '%Y/%m/%d/%H.%M', doc="Default page naming "
                        "scheme for blog posts.")
    new_blog_link_text = Option('blog', 'new_blog_link', 'New Blog Post', doc="Default text for link "
                                "to new blog entry creation.")
    default_tag = ListOption('blog', 'default_tag', 'blog',  doc="Comma separated list of "
                             "tags.  The combination of which are used as the default for "
                             "signifying a blog post.")
    entry_page_title = Option('blog', 'entry_page_title', 'Create Blog Entry', doc="The title used in "
                              "the <title></title> of the blog post entry page.  Also used for the "
                              "title of the post entry page.")
    footer = Option('blog', 'footer', '', doc="Footer to add to each blog post")
    date_format = Option('blog', 'date_format', '%x %X', doc="Date format to use when displaying dates for "
                         "blog entries.  The format is the same as time.strftime()")

    # IPermissionRequestor
    def get_permission_actions(self):
        return ['BLOG_POSTER']

    # WikiMacroBase
    def expand_macro(self, formatter, name, content):
        """ Display the blog in the wiki page """
        if formatter.perm.has_permission('BLOG_POSTER'):
            args, kwargs = parseargs(content)
            try:
                blog_link = kwargs['link']
                del kwargs['link']
            except KeyError:
                blog_link = self.new_blog_link_text
            return tag.a(blog_link, href=formatter.req.href.blog('new',**kwargs))
        return ''

    def match_request(self, req):
        return req.path_info == ENTRY_BASE

    def process_request(self, req):
        req.perm.assert_permission('BLOG_POSTER')
        add_stylesheet(req, 'blog/css/blog.css')
        add_stylesheet(req, 'common/css/wiki.css')
        data = self._new_blog_post(req)
        return 'blog_new.html', data, None

    def _new_blog_post(self, req):
        """ Generate a new blog post """
        action = req.args.get('action', 'edit')
        wikitext = req.args.get('text', '')
        blogtitle = req.args.get('blogtitle', '')
        page_format = req.args.get('pagename', self.page_format) 
        tags = self._get_tags(req)
        referer = self._get_referer(req)

        author = req.authname
        pagename = self._generate_pagename(page_format, blogtitle, author) 
        titleline = ' '.join(["=", blogtitle, "=\n"])

        page = WikiPage(self.env, pagename, None)
        page.text = wikitext
        comment = req.args.get('comment', '')
        readonly = int(req.args.has_key('readonly'))
        edit_rows = req.args.get('edit_rows', '20')
        scroll_bar_pos = req.args.get('scroll_bar_pos', '')
        page_source = page.text

        if blogtitle:
            wikitext = ''.join([titleline, wikitext])

        if req.method == 'POST':
            if action == 'edit':
                if req.args.has_key('cancel'):
                    req.redirect(referer)
                page = WikiPage(self.env, pagename, None)
                tagsystem = TagSystem(self.env)
                # Add footer 
                page.text = ''.join([wikitext, "\n\n", self.var_subs(author, self.footer)]) 
                page.readonly = readonly
                if req.args.has_key('preview'):
                    action = 'preview'
                else:
                    page.save(author, comment, req.remote_addr)
                    tagsystem.set_tags(req, page.resource, tags)
                    req.redirect(referer)

        
        wiki = {'page_name' : pagename,
                'comment' : comment,
                'author' : author,
                'edit_rows' : edit_rows,
                'version' : 0,
                'read_only' : readonly,
                'scroll_bar_pos' : scroll_bar_pos,
                'page_source' : page_source,
                'action' : action,
               }

        data = {'page' : page,
                'action' : action,
                'title' : self.entry_page_title,
                'blog' : {'title' : blogtitle,
                          'pagename' : pagename,
                          'referer' : referer,
                         },
                'tags' : ', '.join(tags),
                'referer' : referer,
               }
        data.update(wiki)
        return data
        

    def _get_tags(self, req):
        """ Return a list of tags.
    
        First look for the presence of the `tags` query argument. If found,
        parse the result into a list.

        Otherwise, look for the `tag` query arguments.

        If none of the previous query arguments exist, use the list of tags
        from `trac.ini`

        """
        taglist = req.args.get('tags', None)
        if taglist:
            tags = [t.strip() for t in _tag_split.split(taglist) if t.strip()]
        elif req.args.has_key('tag'):
            tags = req.args.getlist('tag')
        else:
            tags = self.default_tag
        return tags


    def _generate_pagename(self, page_format, title, author):
        """ Generate a page name based on the format specified.

        All formatting in `time.strftime` is valid along with '%@' for using the blog title
        and '$U' for using the username of the authenticated user.
        """

        pagename = time.strftime(page_format)
        if '%@' in pagename and title: 
            urltitle = re.sub(r'[^\w]+', '-', title).lower() 
            pagename = pagename.replace('%@', urltitle) 
            while '-' in pagename and len(pagename) > 60: 
                pagename = '-'.join(pagename.split('-')[:-1]) 
            pagename = pagename.strip('-')
        if '$U' in pagename:
            username = re.sub(r'[^\w]+', '_', author)
            pagename = pagename.replace('$U', username)
        return pagename

    def _get_referer(self, req):
        """ Return the referring page.

        If the referring page is the new blog entry page, redirect to the main
        blog page.

        Also protects against referring to an external site.

        """
        ref = req.args.get('referer') or req.get_header('Referer') or req.href.blog()
        base_scheme, base_host = urlparse.urlparse(req.base_url)[:2]
        ref_scheme, ref_host = urlparse.urlparse(ref)[:2]
        if ref and (ref.startswith('http://')  or ref.startswith('https://')) \
           and not (ref_host == base_host):
             # don't redirect to external sites
             ref = req.href.blog()
        if urlparse.urlparse(ref)[2] == ENTRY_BASE:
            ref = req.href.blog()
        return ref

    def var_subs(self, author, s): 
        s = s.replace('$U', author) 
        s = s.replace('$D', time.strftime(self.date_format)) 
        return s
    
    # ITemplateProvider
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('blog', resource_filename(__name__, 'htdocs'))]


