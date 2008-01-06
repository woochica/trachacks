# Created by Noah Kantrowitz on 2007-12-20.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from genshi.builder import tag

from trac.core import *
from trac.web.api import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.perm import IPermissionRequestor

class BoxDBModule(Component):
    """Simple document database system to use from Trac."""

    implements(IRequestHandler, INavigationContributor, IPermissionRequestor,
               ITemplateProvider)
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/document')

    def process_request(self, req):
        data = {}
        path_info = req.path_info[10:]
        
        return 'boxdb_edit.html', data, None

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'documents'

    def get_navigation_items(self, req):
        if req.perm.has_permission('DOCUMENT_VIEW'):
            yield 'mainnav', 'documents', tag.a('Documents', href=req.href.document())

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'DOCUMENT_VIEW'

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('boxdb', resource_filename(__name__, 'htdocs'))]
            
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]