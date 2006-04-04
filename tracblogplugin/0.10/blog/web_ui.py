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

import time
import datetime
import inspect
from pkg_resources import resource_filename
from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.web.chrome import INavigationContributor 
from trac.util import Markup, format_date, format_datetime
from trac.wiki.formatter import wiki_to_html, wiki_to_oneliner
from trac.wiki.model import WikiPage
from trac.wiki.api import IWikiMacroProvider
from tractags.api import TagEngine

__all__ = ['TracBlogPlugin']

class TracBlogPlugin(Component):
    """Displays a blog based on tags
    
    The list of tags to be shown can be specified as arguments to the macro.
    An options keyword argument of union can be secified.  If specified, then
    the resulting blog will be a {{{union}}} of pages with the specified tags.
    If the {{{union}}} parameter is omitted, then an intersection of the
    specified tags is returned.

    If no tags are specified as parameters, then the default 'blog' tag is
    used.

    === Examples ===
    {{{
    [[BlogShow()]]
    [[BlogShow(blog,pacopablo)]]
    [[BlogShow(blog,pacopablo,union=True)]]
    }}}
    """

    implements(IRequestHandler, ITemplateProvider, INavigationContributor,
               IWikiMacroProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'blog'
                
    def get_navigation_items(self, req):
        req.hdf['trac.href.blog'] = self.env.href.blog()
        yield 'mainnav', 'blog', Markup('<a href="%s">Blog</a>',
                                         self.env.href.blog())

    # IWikiMacroProvider
    def get_macros(self):
        yield "BlogShow"

    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return inspect.getdoc(self.__class__)

    def render_macro(self, req, name, content):
        """ Display the blog in the wiki page """
        add_stylesheet(req, 'blog/css/blog.css')
        tags, kwargs = self._split_macro_args(content)
        if not tags:
            tags = [self.env.config.get('blog', 'default_tag', 'blog')]
        self._generate_blog(req, *tags, **kwargs)
        req.hdf['blog.macro'] = True
        return req.hdf.render('blog.cs')

    def _split_macro_args(self, argv):
        """Return a list of arguments and a dictionary of keyword arguements

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
        return req.path_info == '/blog'

    def process_request(self, req):
        add_stylesheet(req, 'blog/css/blog.css')
        add_stylesheet(req, 'common/css/wiki.css')
        tags = req.args.getlist('tag')
        kwargs = {}
        for key,value in req.args.items():
            if key != 'tag':
                kwargs[key] = value
            continue
        if not tags:
            tags = [self.env.config.get('blog', 'default_tag', 'blog')]
        self._generate_blog(req, *tags, **kwargs)
        return 'blog.cs', None

    def _generate_blog(self, req, *args, **kwargs):
        """Extract the blog pages and fill the HDF.

        *args is a list of tags to use to limit the blog scope
        **kwargs are any aditional keyword arguments that are needed
        """
        tags = TagEngine(self.env).tagspace.wiki
        try:
            union = kwargs['union']
        except KeyError:
            union = False
        # Formatting
        read_post = "[wiki:%s Read Post]"
        entries = {}
        if not len(args):
            tlist = [self.env.config.get('blog', 'default_tag', 'blog')]
        else:
            tlist = args
        if union:
            blog = tags.get_tagged_names(tlist, operation='union')
        else:
            blog = tags.get_tagged_names(tlist, operation='intersection')
        self.log.debug("blog: %s" % str(blog)) 
        history_days = int(self.env.config.get('blog', 'history_days', 30))
        now = datetime.datetime.now()
        history_diff = datetime.timedelta(days=history_days)
        cutoff = time.mktime((now - history_diff).timetuple())
        for tagspace in blog.keys():
            for blog_entry in blog[tagspace]:
                page = WikiPage(self.env, name=blog_entry)
                version, wtime, author, comment, ipnr = page.get_history(
                                                        ).next()
                if wtime >= cutoff:       
                    time_format = self.env.config.get('blog', 'date_format') \
                                  or '%x %X'
                    timeStr = format_datetime(wtime, format=time_format) 
                    text = self._trim_page(page.text, blog_entry)
                    data = {
                            'wiki_link' : wiki_to_oneliner(read_post % 
                                                           blog_entry,
                                                           self.env),
                            'time'      : timeStr,
                            'author'    : author,
                            'wiki_text' : wiki_to_html(text, self.env, req),
                            'comment'   : wiki_to_oneliner(comment, self.env),
                           }
                    entries[wtime] = data
                continue
        tlist = entries.keys()
        # Python 2.4ism
        # tlist.sort(reverse=True)
        tlist.sort()
        tlist.reverse()
        req.hdf['blog.entries'] = [entries[x] for x in tlist]
        bloglink = self.env.config.get('blog', 'new_blog_link', 'New Blog Post')
        req.hdf['blog.newblog'] = bloglink
        pass

    def _get_time_range(self, req, **kwargs):
        """Return a start and end date range

        Parameters can be passed in via the req object or via **kwargs.  
        **kwargs always overrides the req object.  In practice, this shouldn't
        matter much as the macro will use **kwargs and the nav item will use
        req.  Just documenting behavior.

        The range of days can be specified in multiple ways.
        * Specify date range with startdate and enddate.  Value should be 
          seconds since epoch
        * Specify startdate and delta. delta should be a number of seconds.
        * Specify any combination of year, month, day.  If any one of the
          values is specified, then it will use this method in place of 
          startdate, enddate and delta.  If a value is missing that is required
          such as a year if month is specified, then it deafults to the current
          value.  Otherwise it generates a range according to the values passed
          in.  For example, year=2006 and month=12 will return all posts for 
          December 2006.

        """

    def _trim_page(self, text, page_name):
        """Trim the page text to the {{{post_size}} in trac.ini

        The timming isn't exact.  It trims to the first line that causes the
        page to exceed the value storing in {{{post_size}}}.  If the line is
        in the middle of a code block, it will close the block.

        """
        post_size = int(self.env.config.get('blog', 'post_size', 1024))
        self.log.debug('Post size: %s' % str(post_size))
        tlines = []
        entry_size = 0
        line_count = 0
        in_code_block = False
        lines = text.split('\n')
        for line in lines:
            line_count += 1
            entry_size += len(line)
            tlines.append(line)
            if not in_code_block:
                in_code_block = line.strip() == '{{{'
            else:
                in_code_block = in_code_block and line.strip() != '}}}'
            if entry_size > post_size:
                self.log.debug("Entry Size: %s" % str(entry_size))
                if in_code_block:
                    tlines.append('}}}')
                break
            continue
        if line_count < len(lines):
            tlines.append("''[wiki:%s (...)]''" % page_name)
            
        return '\n'.join(tlines)

    # ITemplateProvider
    def get_templates_dirs(self):
        """ Return the absolute path of the directory containing the provided
            templates

        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """ Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.

        """
        return [('blog', resource_filename(__name__, 'htdocs'))]


