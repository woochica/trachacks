# -*- coding: utf-8 -*-
# Created by Noah Kantrowitz
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
import urllib

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider, add_ctxtnav
from trac.web.api import IRequestFilter
from trac.admin.web_ui import IAdminPanelProvider
from genshi.core import Markup

from wikireplace.util import wiki_text_replace

class WikiReplaceModule(Component):
    """An evil module that adds a replace button to the wiki UI."""
 
    implements(IPermissionRequestor, IAdminPanelProvider, ITemplateProvider,
               IRequestFilter)
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['WIKI_REPLACE']

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        perm = req.perm('wiki')
        if 'WIKI_REPLACE' in perm or 'WIKI_ADMIN' in perm:
            yield ('general', 'General', 'wikireplace', 'Wiki Replace')
            
    def render_admin_panel(self, req, cat, page, path_info):
        data = {
            'find': urllib.unquote_plus(req.args.get('find','')),
            'replace': urllib.unquote_plus(req.args.get('replace','')),
            'redir': req.args.get('redirect','') == '1',
        }
        
        if req.method == 'POST':
            wiki_text_replace(self.env, data['find'], data['replace'], req.authname, req.remote_addr, debug=self.log.debug)

            # Reset for the next display
            data['find'] = ''
            data['replace'] = ''

        return 'admin_wikireplace.html', data
        

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__,'templates')]
        
    def get_htdocs_dirs(self):
        return []
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
            
    def post_process_request(self, req, template, data, content_type):
        if (req.path_info.startswith('/wiki') or req.path_info == '/') and data:
            page = data.get('page')
            if not page:
                return template, data, content_type
            perm = req.perm(page.resource)
        return template, data, content_type
