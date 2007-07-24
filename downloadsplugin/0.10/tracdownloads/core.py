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
    path = Option('downloads', 'path', '/var/lib/trac/downloads',
      'Directory to store uploaded downloads.')

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
        if re.match(r'''^/downloads($|/$)''', req.path_info):
            return True
        if re.match(r'''^/downloads/(\d+)$''',
          req.path_info):
            req.args['action'] = 'get_file'
            return True
        return False

    def process_request(self, req):
        # Create API object.
        self.api = DownloadsApi(self.env)

        # Get cursor.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # CSS styles
        add_stylesheet(req, 'downloads/css/downloads.css')

        # Prepare HDF structure.
        req.hdf['downloads.href'] = req.href.downloads()
        req.hdf['downloads.title'] = self.title

        # Do actions and return content.
        modes = self._get_modes(req)
        self.log.debug('modes: %s' % (modes,))
        content = self._do_actions(req, cursor, modes)
        db.commit()
        return content

    # Private functions.

    def _get_modes(self, req):
        action = req.args.get('action')
        self.log.debug('action: %s' % (action,))
        if action == 'get_file':
            return ['get-file']
        else:
            return ['downloads-list']

    def _do_actions(self, req, cursor, modes):
        for mode in modes:
            if mode == 'get-file':
                req.perm.assert_permission('DOWNLOADS_VIEW')

            elif mode == 'downloads-list':
                req.perm.assert_permission('DOWNLOADS_VIEW')

                # Get form values
                order = req.args.get('order') or 'id'
                desc = req.args.get('desc')

                # Fill HDF structure
                req.hdf['downloads.order'] = order
                req.hdf['downloads.desc'] = desc
                req.hdf['downloads.downloads'] = self.api.get_downloads(req,
                  cursor)

                return 'downloads.cs', None
                #return mode + '.cs', None
