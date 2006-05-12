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

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.perm import IPermissionRequestor
from trac.util import escape, Markup, format_date, format_datetime
from trac.wiki.formatter import wiki_to_html
from webadmin.web_ui import IAdminPageProvider

import os
import os.path
from pkg_resources import resource_filename

__all__ = ['BlogAdminPlugin']

class BlogAdminPlugin(Component):
    """
        Provides functions related to registration
    """

    implements(ITemplateProvider, IAdminPageProvider, IPermissionRequestor)

    # IPermissionRequestor
    def get_permission_actions(self):
        return [('BLOG_ADMIN', ['BLOG_POSTER', 'BLOG_VIEW'])]

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('BLOG_ADMIN'):
            yield ('blog', 'Blog System', 'defaults', 'Defaults')

    def process_admin_request(self, req, cat, page, path_info):
        assert req.perm.has_permission('BLOG_ADMIN')

        add_stylesheet(req, 'blog/css/blog.css')
        add_stylesheet(req, 'common/css/wiki.css')

        req.hdf['blogadmin.page'] = page

        admin_fields = {
                        'date_format'    : '%x %X',
                        'page_format'    : '%Y/%m/%d/%H.%M',
                        'default_tag'    : 'blog', 
                        'post_size'      : 1024,
                        'history_days'   : 30,
                        'new_blog_link'  : 'New Blog Post',
                        'first_week_day' : 'SUNDAY',
                        'mark_updated'   : 'true',
                        'nav_link'       : 'Blog',
                        'nav_bar'        : 'true',
                        'macro_blacklist': '',
                        'rss'            : 'true',
                       }
        if req.method == 'POST':
            if page == 'defaults':
                for field in admin_fields.keys():
                    self._set_field_value(req, field)
                self.env.config.save()
        for field, default in admin_fields.items():
            self._get_field_value(req, field, default)
        req.hdf['blogadmin.docs'] = wiki_to_html(self._get_docs(page),
                                                 self.env, req)
        return 'blog_admin.cs', None

    def _get_docs(self, page):
        """Return the wikitext documentation for the page options. """
        if page == 'defaults':
            doc = """
 '''Date Format String'''::
   string in {{{strftime}}} format
 '''Page Name Format String'''::
   string in {{{strftime}}} format
 '''Default Tag'''::
   tag to use as default when none are specified
 '''Post Max Size'''::
   number of bytes to show before truncating the post and providing a ''(...)'' link.  Posts are truncated at line breaks, and wiki formatting is included in the byte count, so truncation will not be exact.
 '''Days of History'''::
   number of days for which to show blog posts
 '''New Blog Link'''::
   text to show for the new blog link
 '''Calendar Week Start Day'''::
   name of day that acts as the first day of the week.  Must be full day name.
 '''Mark Updated Posts'''::
   whether or not to mark posts that have been updated with an "Updated on" message.
 '''Nav Bar Link Name'''::
   name of the link to show in the nav bar. 
 '''Show Link in Nav Bar'''::
   whether or not a link should be shown in the navigation menu bar.
 '''Macro Blacklist'''::
   comma separated list of macros to strip from blog output.
 '''RSS Feed'''::
   whether or not to enable RSS feeds when using {{{[[BlogShow]]}}}

 '''strftime formatting'''::
||%a||Locale's abbreviated weekday name.||
||%A||Locale's full weekday name.||
||%b||Locale's abbreviated month name.||
||%B||Locale's full month name.||
||%c||Locale's appropriate date and time representation.||
||%d||Day of the month as a decimal number [01,31].||
||%H||Hour (24-hour clock) as a decimal number [00,23].||
||%I||Hour (12-hour clock) as a decimal number [01,12].||
||%j||Day of the year as a decimal number [001,366].||
||%m||Month as a decimal number [01,12].||
||%M||Minute as a decimal number [00,59].||
||%p||Locale's equivalent of either AM or PM.||
||%S||Second as a decimal number [00,61].||
||%U||Week number of the year (Sunday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Sunday are considered to be in week 0.||
||%w||Weekday as a decimal number [0(Sunday),6].||
||%W||Week number of the year (Monday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Monday are considered to be in week 0.||
||%x||Locale's appropriate date representation.||
||%X||Locale's appropriate time representation.||
||%y||Year without century as a decimal number [00,99].||
||%Y||Year with century as a decimal number.||
||%Z||Time zone name (no characters if no time zone exists).||
||%%||A literal "%" character.||
||%@||An URL friendly version of the Blog Entry Title||
||$U||Name of the current user||

"""
        return doc
        

    def _set_field_value(self, req, field_name, default=None):
        """Set the trac.ini field value for the specified name. """
        if field_name in req.args:
            field = req.args.get(field_name)
            self.env.config.set('blog', field_name, field)
        pass

    def _get_field_value(self, req, field_name, default=None):
        """Get the field from trac.ini and set the hdf appropriately. """
        field = self.env.config.get('blog', field_name) or default
        req.hdf['blogadmin.' + field_name] = field
        pass

    # INavigationContributor
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

