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
from pkg_resources import resource_filename

from genshi.builder import tag

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.perm import IPermissionRequestor
from trac.util import Markup
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html
from trac.wiki.model import WikiPage
from trac.wiki.macros import WikiMacroBase
from trac.config import Option
from trac.resource import *

from tBlog.parseargs import parseargs

#from tractags.api import TagEngine
#from tractags.parseargs import parseargs

__all__ = ['BlogPost']

_tag_split = re.compile('[,\s]+')

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

    implements(IRequestHandler, ITemplateProvider, IWikiMacroProvider, 
               IPermissionRequestor)

    page_format = Option('blog', 'page_format', '%Y/%m/%d/%H.%M', doc="Default page naming "
                        "scheme for blog posts.")

    # IPermissionRequestor
    def get_permission_actions(self):
        return ['BLOG_POSTER']

    # WikiMacroBase
    def expand_macro(self, formatter, name, content):
        """ Display the blog in the wiki page """
        if formatter.perm.has_permission('BLOG_POSTER'):
            args, kwargs = self._split_macro_args(content)
            try:
                blog_link = kwargs['link']
                del kwargs['link']
            except KeyError:
                blog_link = self.env.config.get('blog', 'new_blog_link', 
                                                'New Blog Post')
            return tag.a(blog_link, href=formatter.req.href.blog('new',**kwargs))
        return ''

    def _split_macro_args(self, argv):
        """Return a list of arguments and a dictionary of keyword arguments

        """
        args = []
        kwargs = {}
        if argv:
            args, kwargs = parseargs(argv)
        return args, kwargs

    def match_request(self, req):
        return req.path_info == '/blog/new'

    def process_request(self, req):
        req.perm.assert_permission('BLOG_POSTER')
        add_stylesheet(req, 'blog/css/blog.css')
        add_stylesheet(req, 'common/css/wiki.css')
#        self._new_blog_post(req)
        referer = req.args.get('referer') or req.get_header('Referer') or req.href.blog()
        data = self._new_blog_post(req)
        data['blog']['referer'] =  referer
        return 'blog_new.html', data, None

    def _new_blog_post(self, req):
        """ Generate a new blog post """
        action = req.args.get('action', 'edit')
        wikitext = req.args.get('text', '')
        blogtitle = req.args.get('blogtitle', '')
        page_format = req.args.get('page_format', self.page_format) 
        pagename = self._generate_pagename(page_format, blogtitle, req.authname) 
        page = WikiPage(self.env, pagename, None)

        comment = req.args.get('comment', '')
        readonly = int(req.args.has_key('readonly'))
        edit_rows = int(req.args.get('edit_rows', 20))
        scroll_bar_pos = req.args.get('scroll_bar_pos', '')
        req_tags = req.args.get('tags', [])
        page_source = page.text

        title = get_resource_summary(self.env, page.resource)
        if action:
            title += ' (%s)' % action

        wiki = {'page_name' : pagename,
                'comment' : comment,
                'author' : req.authname,
                'edit_rows' : edit_rows,
                'version' : 0,
                'read_only' : readonly,
                'scroll_bar_pos' : scroll_bar_pos,
                'page_source' : page_source,
                'action' : action,
               }

        data = {'page' : page,
                'action' : action,
                'title' : title,
                'blog' : {},
               }
        data.update(wiki)
        return data
        
#        if req.method == 'POST':
#            if action == 'edit':
#                if req.args.has_key('cancel'):
#                    referrer = req.args.get('referer') or req.get_header('Referer') or self.env.href.blog()
#                    req.redirect(referrer)
#                page = WikiPage(self.env, pagename, None)
#                tags = TagEngine(self.env).tagspace.wiki
#                if req.args.has_key('preview'):
#                    req.hdf['blog.action'] = 'preview'
#                    self._render_editor(req, page, self.env.get_db_cnx(),
#                                        preview=True) 
#                else:
#                    titleline = ' '.join(["=", blogtitle, "=\n"])
#                    if blogtitle:
#                        page.text = ''.join([titleline, wikitext])
#                    else:
#                        page.text = wikitext
#                    # Add footer 
#                    page.text = page.text.join(["\n\n",self.variable_substitution(req,self.env.config.get('blog', 'footer', ''))]) 
#                    page.readonly = readonly
#                    page.save(req.authname, comment, req.remote_addr)
#                    taglist = [x.strip() for x in req_tags.split(',') if x]
#                    taglist = [t.strip() for t in 
#                               _tag_split.split(req.args.get('tags')) 
#                               if t.strip()]
#                    tags.add_tags(req, pagename, taglist)
#                    referrer = req.args.get('referer') or req.get_header('Referer') or self.env.href.blog()
#                    req.redirect(referrer)
#        else:
#            info = {
#                'title' : blogtitle,
#                'pagename': pagename,
#                'page_source': wikitext,
#                'comment': comment,
#                'readonly': readonly,
#                'edit_rows': edit_rows,
#                'scroll_bar_pos': req.args.get('scroll_bar_pos', '')
#            }
#            req.hdf['blog'] = info
#            req.hdf['title'] = 'New Blog Entry'
#            tlist = req.args.getlist('tag')
#            if not tlist:
#                tlist = [self.env.config.get('blog', 'default_tag', 'blog')]
#            req.hdf['tags'] = ', '.join(tlist)
#            pass

    def _generate_pagename(self, page_format, title, authname):
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
            pagename = pagename.replace('$U', authname)
        return pagename

#    def _render_editor(self, req, page, db, preview=False):
#        blogtitle = req.args.get('blogtitle')
#        titleline = ' '.join(["=", blogtitle, "=\n"])
#        if req.args.has_key('text'):
#            page.text = req.args.get('text')
#        if preview:
#            page.readonly = req.args.has_key('readonly')
#
#        author = req.authname
#        comment = req.args.get('comment', '')
#        editrows = req.args.get('editrows')
#        tags = req.args.get('tags')
#        req.hdf['tags'] = tags
#        if editrows:
#            pref = req.session.get('wiki_editrows', '20')
#            if editrows != pref:
#                req.session['wiki_editrows'] = editrows
#        else:
#            editrows = req.session.get('wiki_editrows', '20')
#
#        req.hdf['title'] = page.name + ' (edit)'
#        info = {
#            'title' : blogtitle,
#            'pagename': page.name,
#            'page_source': page.text,
#            'author': author,
#            'comment': comment,
#            'readonly': page.readonly,
#            'edit_rows': editrows,
#            'scroll_bar_pos': req.args.get('scroll_bar_pos', '')
#        }
#        if preview:
#            if blogtitle:
#                info['page_html'] = wiki_to_html(''.join([titleline, 
#                                                 req.args.get('text'), 
#                                                 "\n\n",self.variable_substitution(req,self.env.config.get('blog', 'footer', ''))]), 
#                                                self.env, req, db)
#            else:
#                info['page_html'] = wiki_to_html(page.text.join(["\n\n",
#                    self.variable_substitution(req,self.env.config.get('blog', 'footer', ''))]), 
#                                                  self.env, 
#                                                  req, 
#                                                  db) 
#            info['readonly'] = int(req.args.has_key('readonly'))
#        req.hdf['blog'] = info

    def variable_substitution(self,req,string): 
        string = string.replace('$U',req.authname) 
        string = string.replace('$D',time.strftime(self.env.config.get('blog', 'date_format', '%x %X'))) 
        return string 
    
    # ITemplateProvider
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('blog', resource_filename(__name__, 'htdocs'))]


