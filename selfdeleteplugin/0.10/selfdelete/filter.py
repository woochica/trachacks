from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor
from trac.wiki.model import WikiPage
from trac.attachment import Attachment, AttachmentModule

__all__ = ['SelfDeleteModule']

class SelfDeleteModule(Component):
    """Plugin to allow deleting wiki pages and attachments you created."""
    
    implements(INavigationContributor, IPermissionRequestor)
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return ''
    
    def get_navigation_items(self, req):
        if req.authname != 'anonymous':
            self._alter_req(req)        
        return []
        
    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'WIKI_DELETE_SELF'
        yield 'TICKET_DELETE_SELF'

    # Internal methods
    def _alter_req(self, req):
        alter = False
        if req.path_info.startswith('/wiki/'):
            if not req.perm.has_permission('WIKI_DELETE_SELF') or \
               req.perm.has_permission('WIKI_DELETE'):
                return # Not allowed
        
            pagename = req.path_info[6:] or 'WikiStart'
            page = WikiPage(self.env, pagename, version=1)
            
            if not page.exists: return # Sanity check
            
            if req.authname == page.author:
                alter = 'WIKI_DELETE'
        elif AttachmentModule(self.env).match_request(req):
            parent_type = req.args.get('type')
            path = req.args.get('path')
            if req.args.get('action') == 'new':
                return # Delete permissions don't matter for this anyway
                
            needed_perm = {'ticket': 'TICKET_DELETE', 'wiki': 'WIKI_DELETE'}[parent_type]
            if not req.perm.has_permission(needed_perm+'_SELF') or \
               req.perm.has_permission(needed_perm):
                return # Not allowed 
                
            segments = path.split('/')
            parent_id = '/'.join(segments[:-1])
            last_segment = segments[-1]
            if len(segments) == 1:
                return # List view, don't care about this
            
            try:
                attachment = Attachment(self.env, parent_type, parent_id, last_segment)
            except TracError:
                return # Sanity check
            
            if req.authname == attachment.author:
                alter = needed_perm
            
        if alter:
            self.log.info('SelfDeleteModule: Allowing user %s to delete the resource at %s.', req.authname, req.path_info)
            req.perm.perms[alter] = True
            req.hdf['trac.acl.%s'%alter] = '1'
                   
    
