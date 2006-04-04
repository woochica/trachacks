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
        return ['BLOG_ADMIN']

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
                        'date_format'  : '%x %X',
                        'page_format'  : '%Y/%m/%d/%H.%M',
                        'default_tag'  : 'blog', 
                        'post_size'    : 1024,
                        'history_days' : 30,
                        'new_blog_link' : 'New Blog Post',
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

