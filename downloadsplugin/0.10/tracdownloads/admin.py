from tracdownloads.api import *
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import add_stylesheet
from trac.wiki import wiki_to_html, wiki_to_oneliner
from webadmin.web_ui import IAdminPageProvider
import time

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
            yield ('downloads', 'Downloads System', 'architectures', 'Architectures')
	    yield ('downloads', 'Downloads System', 'platforms', 'Platforms')
	    yield ('downloads', 'Downloads System', 'types', 'Types')

    def process_admin_request(self, req, category, page, path_info):
        # Create API object
        api = DownloadsApi(self, req)
	
        return None
