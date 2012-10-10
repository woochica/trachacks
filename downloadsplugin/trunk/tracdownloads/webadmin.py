# -*- coding: utf-8 -*-

from trac.core import *
from trac.mimeview import Context
from trac.admin import IAdminPanelProvider

from tracdownloads.api import *

class DownloadsWebAdmin(Component):
    """
        The webadmin module implements downloads plugin administration
        via WebAdminPlugin.
    """
    implements(IAdminPanelProvider)

    # IAdminPageProvider

    def get_admin_panels(self, req):
        if req.perm.has_permission('DOWNLOADS_ADMIN'):
            yield ('downloads', 'Downloads System', 'downloads', 'Downloads')
            yield ('downloads', 'Downloads System', 'architectures',
              'Architectures')
            yield ('downloads', 'Downloads System', 'platforms', 'Platforms')
            yield ('downloads', 'Downloads System', 'types', 'Types')

    def render_admin_panel(self, req, category, page, path_info):
        # Create request context.
        context = Context.from_request(req)('downloads-admin')

        # Set page name to request.
        req.args['page'] = page
        if page == 'architectures':
            req.args['architecture'] = path_info
        elif page == 'platforms':
            req.args['platform'] = path_info
        elif page == 'types':
            req.args['type'] = path_info
        elif page == 'downloads':
            req.args['download'] = path_info

        # Process request and return content.
        api = self.env[DownloadsApi]
        return api.process_downloads(context)
