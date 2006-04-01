from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider
from trac.util import escape, Markup, format_date, format_datetime
from webadmin.web_ui import IAdminPageProvider

import os
import os.path
from pkg_resources import resource_filename

__all__ = ['BlogAdminPlugin']

class BlogAdminPlugin(Component):
    """
        Provides functions related to registration
    """

    implements(ITemplateProvider, IAdminPageProvider)

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('BLOG_ADMIN'):
            yield ('blog', 'Blog System', 'formats', 'Formats')

    def process_admin_request(self, req, cat, page, path_info):
        assert req.perm.has_permission('BLOG_ADMIN')

#        req.hdf['ticketdelete.href'] = self.env.href('admin', cat, page)
        req.hdf['blogadmin.page'] = page
#        req.hdf['ticketdelete.redir'] = 1

        if req.method == 'POST':
            if page == 'formats':
                if 'date_format' in req.args:
                    date_format = req.args.get('date_format')
                    self.env.config.set('blog', 'date_format', date_format)
                if 'page_format' in req.args:
                    page_format = req.args.get('page_format')
                    self.env.config.set('blog', 'page_format', page_format)
                self.env.config.save()
        date_format = self.env.config.get('blog', 'date_format')
        page_format = self.env.config.get('blog', 'page_format')
        req.hdf['blogadmin.date_format'] = date_format
        req.hdf['blogadmin.page_format'] = page_format
        return 'blog_admin.cs', None

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
        return [('pyrus', resource_filename(__name__, 'htdocs'))]

