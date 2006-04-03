from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider
from trac.perm import IPermissionRequestor
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

        req.hdf['blogadmin.page'] = page

        admin_fields = ['date_format', 'page_format', 'default_tag', 
                        'post_size', 'history_days', ]
        if req.method == 'POST':
            if page == 'defaults':
                for field in admin_fields:
                    self._set_field_value(req, field)
                self.env.config.save()
        for field in admin_fields:
            self._get_field_value(req, field)
        return 'blog_admin.cs', None

    def _set_field_value(self, req, field_name):
        """Set the trac.ini field value for the specified name. """
        if field_name in req.args:
            field = req.args.get(field_name)
            self.env.config.set('blog', field_name, field)
        pass

    def _get_field_value(self, req, field_name):
        """Get the field from trac.ini and set the hdf appropriately. """
        field = self.env.config.get('blog', field_name)
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
        return [('pyrus', resource_filename(__name__, 'htdocs'))]

