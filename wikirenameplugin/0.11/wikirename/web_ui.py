# Created by Noah Kantrowitz
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
import urllib

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider, add_ctxtnav
from trac.web.api import IRequestFilter
from trac.admin.web_ui import IAdminPanelProvider
from genshi.core import Markup

from wikirename.util import rename_page

class WikiRenameModule(Component):
    """An evil module that adds a rename button to the wiki UI."""
 
    implements(IPermissionRequestor, IAdminPanelProvider, ITemplateProvider,
               IRequestFilter)
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['WIKI_RENAME']

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        perm = req.perm('wiki')
        if 'WIKI_RENAME' in perm or 'WIKI_ADMIN' in perm:
            yield ('general', 'General', 'wikirename', 'Wiki Rename')
            
    def render_admin_panel(self, req, cat, page, path_info):
        data = {
            'src': urllib.unquote_plus(req.args.get('src_page','')),
            'dest': urllib.unquote_plus(req.args.get('dest_page','')),
            'redir': req.args.get('redirect','') == '1',
        }
        
        if req.method == 'POST':
            if not data['src'] or not data['dest']:
                raise TracError, "Please provide both the old and new names"
            rename_page(self.env, data['src'], data['dest'], req.authname, req.remote_addr, debug=self.log.debug)
            if data['redir']:
                req.redirect(req.href.wiki(data['dest']))
            # Reset for the next display
            data['src'] = ''
            data['dest'] = ''

        return 'admin_wikirename.html', data
        

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
            page = data['page']
            perm = req.perm(page.resource)
            if 'WIKI_RENAME' in perm or 'WIKI_ADMIN' in perm:
                href = req.href.admin('general','wikirename', 
                                      redirect='1', src_page=page.name)
                add_ctxtnav(req, 'Rename page', href)
        return template, data, content_type
