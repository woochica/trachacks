from trac.core import *
from trac.util import Markup
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider
from webadmin.web_ui import IAdminPageProvider

from wikirename.util import rename_page

_implements = [IPermissionRequestor, IAdminPageProvider, ITemplateProvider]

try:
    from ctxtnavadd.api import ICtxtnavAdder
    _implements.append(ICtxtnavAdder)
except ImportError:
    pass

class WikiRenameModule(Component):
    """An evil module that adds a rename button to the wiki UI."""
 
    implements(*_implements)
    
    # ICtxtnavAdder methods
    def match_ctxtnav_add(self, req):
        perm = req.perm.has_permission('WIKI_RENAME') or req.perm.has_permission('WIKI_ADMIN')
        return req.path_info.startswith('/wiki') and perm
        
    def get_ctxtnav_adds(self, req):
        page = req.path_info[6:] or 'WikiStart'
        yield (req.href.admin('general','wikirename')+'?redirect=1&src_page='+page,'Rename page')

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['WIKI_RENAME']

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('WIKI_RENAME') or req.perm.has_permission('WIKI_ADMIN'):
            yield ('general', 'General', 'wikirename', 'Wiki Rename')
            
    def process_admin_request(self, req, cat, page, path_info):
        src = req.args.get('src_page','')
        dest = req.args.get('dest_page','')
        redir = req.args.get('redirect','') == '1'
        
        if 'submit' in req.args.keys():
            if not src or not dest:
                raise TracError, "Please provide both the old and new names"
            rename_page(self.env, src, dest, req.authname, req.remote_addr)
            if redir:
                req.redirect(req.href.wiki(dest))
            # Reset for the next display
            src = ''
            dest = ''

        req.hdf['wikirename.src'] = src
        req.hdf['wikirename.dest'] = dest
        req.hdf['wikirename.redir'] = redir
        return 'wikirename_admin.cs', None
        

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__,'templates')]
        
    def get_htdocs_dirs(self):
        return []
