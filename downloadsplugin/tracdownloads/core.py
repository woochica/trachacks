from tracdownloads.api import *
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.config import Option
from trac.util import format_datetime, TracError
from trac.util.html import html
import re, os, os.path, time, mimetypes
from tractags.api import TagEngine

class DownloadsCore(Component):
    """
        The core module implements plugin's main page and mainnav button,
        provides permissions and templates.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
      IPermissionRequestor)

    title = Option('downloads', 'title', 'Downloads',
      'Main navigation bar button title.')
    path = Option('downloads', 'path', '/var/lib/trac/downloads'
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
        self.api = DownloadsApi(self)

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
        elif action == 'add':
            return ['add', 'add-display']
        elif action == 'post-add':
            return ['post-add', 'display']
        elif action == 'edit':
            return ['edit', 'add-display']
        elif action == 'post-edit':
            return ['post-edit', 'display']
        elif action == 'delete':
            return ['delete', 'display']
        else:
            return ['display']

    def _do_actions(self, req, cursor, modes):
        for mode in modes:
            if mode == 'get-file':
                req.perm.assert_permission('DOWNLOADS_VIEW')

            elif mode == 'add':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

            elif mode == 'post-add':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

            elif mode == 'edit':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

            elif mode == 'post-edit':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

            elif mode == 'delete':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

            elif mode == 'display':
                req.perm.assert_permission('DOWNLOADS_VIEW')

                return 'downloads.cs', None

            elif mode == 'add-display':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                return 'downloads-add.cs', None

    def _get_file_from_req(self, req):
        image = req.args['image']

        # Test if file is uploaded.
        if not hasattr(image, 'filename') or not image.filename:
            raise TracError('No file uploaded.')
        if hasattr(image.file, 'fileno'):
            size = os.fstat(image.file.fileno())[6]
        else:
            size = image.file.len
        if size == 0:
            raise TracError('Can\'t upload empty file.')

        return image.file, image.filename
