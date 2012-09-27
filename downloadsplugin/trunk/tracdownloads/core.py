# -*- coding: utf-8 -*-

# Standard imports.
import re

# Trac imports
from trac.core import *
from trac.config import Option
from trac.mimeview import Context
from trac.util.html import html
from trac.util.text import pretty_size
from trac.util.translation import domain_functions

# Trac interfaces.
from trac.web.main import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.resource import IResourceManager
from trac.perm import IPermissionRequestor

# Local imports.
from tracdownloads.api import *

# Bring in dedicated Trac plugin i18n helper.
add_domain, _, tag_ = domain_functions('tracdownloads', ('add_domain', '_',
  'tag_'))

class DownloadsCore(Component):
    """
        The core module implements plugin's ability to download files, provides
        permissions and templates.
    """
    implements(IRequestHandler, ITemplateProvider, IPermissionRequestor,
      IResourceManager)

    # IPermissionRequestor methods.

    def get_permission_actions(self):
        view = 'DOWNLOADS_VIEW'
        add = ('DOWNLOADS_ADD', ['DOWNLOADS_VIEW'])
        admin = ('DOWNLOADS_ADMIN', ['DOWNLOADS_VIEW', 'DOWNLOADS_ADD'])
        return [view, add, admin]

    # ITemplateProvider methods.

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('downloads', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IRequestHandler methods.

    def match_request(self, req):
        match = re.match(r'''^/downloads/(\d+)($|/$)''', req.path_info)
        if match:
            req.args['action'] = 'get-file'
            req.args['id'] = match.group(1)
            return True
        match = re.match(r'''^/downloads/([^/]+)($|/$)''', req.path_info)
        if match:
            req.args['action'] = 'get-file'
            req.args['file'] = match.group(1)
            return True
        return False

    def process_request(self, req):
        # Create request context.
        context = Context.from_request(req)('downloads-core')

        # Process request and return content.
        api = self.env[DownloadsApi]
        return api.process_downloads(context) + (None,)

    # IResourceManager methods.

    def get_resource_realms(self):
        yield 'downloads'

    def get_resource_url(self, resource, href, **kwargs):
        return href.downloads(resource.id)

    def get_resource_description(self, resource, format = 'default',
      context = None, **kwargs):
        # Create context.
        context = Context('downloads-core')
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Get download from ID.
        api = self.env[DownloadsApi]
        download = api.get_download(context, resource.id)

        if format == 'compact':
            return download['file']
        elif format == 'summary':
            return '(%s) %s' % (pretty_size(download['size']),
              download['description'])
        return download['file']

class DownloadsDownloads(Component):
    """
        The downloads module implements plugin's main page and mainnav button.
    """
    implements(INavigationContributor, IRequestHandler)

    # Configuration options.
    title = Option('downloads', 'title', 'Downloads',
      doc = 'Main navigation bar button title.')

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
        match = re.match(r'''^/downloads/([^/]+)($|/$)''', req.path_info)
        if match:
            req.args['action'] = 'get-file'
            req.args['file'] = match.group(1)
            return True
        return False

    def process_request(self, req):
        # Create request context.
        context = Context.from_request(req)('downloads-downloads')

        # Process request and return content.
        api = self.env[DownloadsApi]
        return api.process_downloads(context) + (None,)
