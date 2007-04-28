from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider
from trac.admin.web_ui import IAdminPanelProvider
from genshi.core import Markup

from wikirename.util import rename_page

import urllib

class WikiRenameModule(Component):
    """An evil module that adds a rename button to the wiki UI."""
 
    implements(IPermissionRequestor, IAdminPanelProvider, ITemplateProvider)
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['WIKI_RENAME']

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('WIKI_RENAME') or req.perm.has_permission('WIKI_ADMIN'):
            yield ('general', 'General', 'wikirename', 'Wiki Rename')
            
    def render_admin_panel(self, req, cat, page, path_info):
        data = {
            'src': urllib.unquote_plus(req.args.get('src_page','')),
            'dest': urllib.unquote_plus(req.args.get('dest_page','')),
            'redir': req.args.get('redirect','') == '1',
        }
        
        if 'submit' in req.args.keys():
            if not src or not dest:
                raise TracError, "Please provide both the old and new names"
            rename_page(self.env, data['src'], data['dest'], req.authname, req.remote_addr, debug=self.log.debug)
            if data['redir']:
                req.redirect(req.href.wiki(dest))
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
