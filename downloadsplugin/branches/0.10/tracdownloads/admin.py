# -*- coding: utf8 -*-

from trac.core import *

from webadmin.web_ui import IAdminPageProvider

from tracdownloads.api import *

class DownloadsWebAdmin(Component):
    """
        The webadmin module implements downloads plugin administration
        via WebAdminPlugin.
    """
    implements(IAdminPageProvider)

    # IAdminPageProvider

    def get_admin_pages(self, req):
        if req.perm.has_permission('DOWNLOADS_ADMIN'):
            yield ('downloads', 'Downloads System', 'downloads', 'Downloads')
            yield ('downloads', 'Downloads System', 'architectures',
              'Architectures')
            yield ('downloads', 'Downloads System', 'platforms', 'Platforms')
            yield ('downloads', 'Downloads System', 'types', 'Types')

    def process_admin_request(self, req, category, page, path_info):
        # Get cursor.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Prepare arguments and HDF structure.
        req.args['context'] = 'admin'
        req.args['page'] = page
        if page == 'architectures':
            req.args['architecture'] = path_info
        elif page == 'platforms':
            req.args['platform'] = path_info
        elif page == 'types':
            req.args['type'] = path_info
        elif page == 'downloads':
            req.args['download'] = path_info

        # Return page content.
        api = self.env[DownloadsApi]
        content = api.process_downloads(req, cursor)
        db.commit()
        return content
