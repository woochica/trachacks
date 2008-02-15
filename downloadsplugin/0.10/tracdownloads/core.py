# -*- coding: utf8 -*-

import re

from trac.core import *
from trac.config import Option
from trac.web.chrome import add_stylesheet
from trac.util import format_datetime, TracError
from trac.util.html import html

from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider

from tracdownloads.api import *

class DownloadsCore(Component):
    """
        The core module implements plugin's main page and mainnav button,
        provides permissions and templates.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
      IPermissionRequestor)

    title = Option('downloads', 'title', 'Downloads',
      'Main navigation bar button title.')

    # IPermissionRequestor methods.

    def get_permission_actions(self):
        return ['DOWNLOADS_VIEW', 'DOWNLOADS_ADMIN',]

    # ITemplateProvider methods.

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('downloads', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods.
    def get_active_navigation_item(self, req):
        return 'downloads'

    def get_navigation_items(self, req):
        if req.perm.has_permission('DOWNLOADS_VIEW'):
            yield 'mainnav', 'downloads', html.a(self.title,
              href = req.href.downloads())

    # IRequestHandler methods.

    def match_request(self, req):
        match = re.match(r'''^/downloads($|/$)''', req.path_info)
        if match:
            return True
        match = re.match(r'''^/downloads/(\d+)($|/$)''', req.path_info)
        if match:
            req.args['action'] = 'get-file'
            req.args['id'] = match.group(1)
            return True
        return False

    def process_request(self, req):
        # Get cursor.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Prepare arguments and HDF structure.
        req.args['context'] = 'core'

        # Return page content.
        api = self.env[DownloadsApi]
        content = api.process_downloads(req, cursor)
        db.commit()
        return content
