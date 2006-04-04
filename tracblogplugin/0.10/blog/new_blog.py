# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 John Hampton <pacopablo@asylumware.com>
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
# Author: John Hampton <pacopablo@asylumware.com>
import os
import os.path
import time
import inspect
from pkg_resources import resource_filename
from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.perm import IPermissionRequestor
from trac.util import Markup, doctrim
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html
from trac.wiki.model import WikiPage
from tractags.api import TagEngine

__all__ = ['BlogPost']

class BlogPost(Component):
    """Inserts a link to create a new blog post

    Accepts keyword arguments that specify default parameters. 

    '''tag''' - Tag that populates the "Tag under" field.  This key may be 
    specified multiple times.[[br]]
    '''blogtitle''' - Default blog entry title.[[br]]
    '''text''' - Default entry body text.[[br]]
    '''pagename''' - Default wiki page name.[[br]]
    '''readonly''' - Default readonly page status.[[br]]

    === Examples ===
    {{{
    [[BlogPost()]]
    [[BlogPost(tag=blog,tag=pacopablo)]]
    [[BlogPost(tag=blog,blogtitle=A Simple Title,text=Body Text)]]
    [[BlogPost(tag=blog,pagename=blog/newpage,readonly=1)]]
    }}}
    """

    implements(IRequestHandler, ITemplateProvider, IWikiMacroProvider, 
               IPermissionRequestor)

    # IPermissionRequestor
    def get_permission_actions(self):
        return ['BLOG_POSTER']

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('BLOG_ADMIN'):
            yield ('blog', 'Blog System', 'defaults', 'Defaults')



    # IWikiMacroProvider
    def get_macros(self):
        yield "BlogPost"

    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return inspect.getdoc(self.__class__)

    def render_macro(self, req, name, content):
        """ Display the blog in the wiki page """
        if req.perm.has_permission('BLOG_POSTER'):
            add_stylesheet(req, 'blog/css/blog.css')
            args, kwargs = self._split_macro_args(content)
            try:
                blog_link = kwargs['link']
            except KeyError:
                blog_link = self.env.config.get('blog', 'new_blog_link', 
                                                'New Blog Post')
            return Markup('<a href="%s">%s</a>', 
                          self.env.href.blog('new',**kwargs),
                          blog_link)
        return ''

    def _split_macro_args(self, argv):
        """Return a list of arguments and a dictionary of keyword arguments

        """
        argv = argv or ''
        parms = [x.strip() for x in argv.split(',') if x]
        self.log.debug("parms: %s" % str(parms))
        kargs = [x for x in parms if x.find('=') >= 0]
        self.log.debug("kargs: %s" % str(kargs))
        args = [x for x in parms if x not in kargs]
        self.log.debug("args: %s" % str(args))
        kwargs = {}
        for x in kargs:
            key, value = x.split('=')
            key = key.strip()
            value = value.strip()
            if isinstance(key, unicode):
                key = key.encode('ascii')
                value = value.encode('ascii')
            if kwargs.has_key(key):
                if isinstance(key, list):
                    kwargs[key].append(value)
                else:
                    kwargs[key] = [kwargs[key], value]
            else:
                kwargs[key] = value
        self.log.debug("kwargs: %s" % str(kwargs))
        return args, kwargs

    def match_request(self, req):
        return req.path_info == '/blog/new'

    def process_request(self, req):
        add_stylesheet(req, 'blog/css/blog.css')
        add_stylesheet(req, 'common/css/wiki.css')
        self._new_blog_post(req)
        return 'new_blog.cs', None

    def _new_blog_post(self, req):
        """ Generate a new blog post

        """
        action = req.args.get('action', 'edit')
        pg_name_fmt = self.env.config.get('blog', 'page_format', 
                                          '%Y/%m/%d/%H.%M')
        pagename = req.args.get('pagename', time.strftime(pg_name_fmt))
        wikitext = req.args.get('text', '')
        blogtitle = req.args.get('blogtitle', '')
        comment = req.args.get('comment', '')
        readonly = int(req.args.has_key('readonly'))
        edit_rows = int(req.args.get('edite_rows', 20))
        req_tags = req.args.get('tags', [])

        if req.method == 'POST':
            if action == 'edit':
                if req.args.has_key('cancel'):
                    req.redirect(self.env.href.blog())
                page = WikiPage(self.env, pagename, None)
                tags = TagEngine(self.env).tagspace.wiki
                if req.args.has_key('preview'):
                    req.hdf['blog.action'] = 'preview'
                    self._render_editor(req, page, self.env.get_db_cnx(),
                                        preview=True) 
                else:
                    titleline = ' '.join(["=", blogtitle, "=\n"])
                    if blogtitle:
                        page.text = ''.join([titleline, wikitext])
                    else:
                        page.text = wikitext
                    page.readonly = readonly
                    page.save(req.authname, comment, req.remote_addr)
                    taglist = [x.strip() for x in req_tags.split(',') if x]
#                    for t in taglist:
#                        tags.add_tags(req, pagename, t)
                    tags.add_tags(req, pagename, taglist)
                    req.redirect(self.env.href.blog())
        else:
            info = {
                'title' : blogtitle,
                'pagename': pagename,
                'page_source': wikitext,
                'comment': comment,
                'readonly': readonly,
                'edit_rows': edit_rows,
                'scroll_bar_pos': req.args.get('scroll_bar_pos', '')
            }
            req.hdf['blog'] = info
            req.hdf['title'] = 'New Blog Entry'
            tlist = req.args.getlist('tag')
            if not tlist:
                tlist = [self.env.config.get('blog', 'default_tag', 'blog')]
            req.hdf['tags'] = ', '.join(tlist)
            pass

    def _render_editor(self, req, page, db, preview=False):
        blogtitle = req.args.get('blogtitle')
        titleline = ' '.join(["=", blogtitle, "=\n"])
        if req.args.has_key('text'):
            page.text = req.args.get('text')
        if preview:
            page.readonly = req.args.has_key('readonly')

        author = req.authname
        comment = req.args.get('comment', '')
        editrows = req.args.get('editrows')
        tags = req.args.get('tags')
        req.hdf['tags'] = tags
        if editrows:
            pref = req.session.get('wiki_editrows', '20')
            if editrows != pref:
                req.session['wiki_editrows'] = editrows
        else:
            editrows = req.session.get('wiki_editrows', '20')

        req.hdf['title'] = page.name + ' (edit)'
        info = {
            'title' : blogtitle,
            'pagename': page.name,
            'page_source': page.text,
            'author': author,
            'comment': comment,
            'readonly': page.readonly,
            'edit_rows': editrows,
            'scroll_bar_pos': req.args.get('scroll_bar_pos', '')
        }
        if preview:
            if blogtitle:
                info['page_html'] = wiki_to_html(''.join([titleline, 
                                                req.args.get('text')]),
                                                self.env, req, db)
            else:
                info['page_html'] = wiki_to_html(page.text, self.env, req, db)
            info['readonly'] = int(req.args.has_key('readonly'))
        req.hdf['blog'] = info

    
    # ITemplateProvider
    def get_templates_dirs(self):
        """
            Return the absolute path of the directory containing the provided
            templates
        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return [('blog', resource_filename(__name__, 'htdocs'))]


