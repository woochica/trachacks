from trac.core import *
from trac.web.main import _open_environment
from trac.perm import PermissionSystem

from webadmin.web_ui import IAdminPageProvider

from api import DatamoverSystem

class DatamoverPermissionModule(Component):
    """The permission moving component of the datamover plugin."""

    implements(IAdminPageProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('mover', 'Data Mover', 'permission', 'Permissions')
    
    def process_admin_request(self, req, cat, page, path_info):
        envs = DatamoverSystem(self.env).all_environments()
        permissions = PermissionSystem(self.env).get_all_permissions()
        
        if req.method == 'POST':
            source_type = req.args.get('source')
            if not source_type or source_type not in ('permission', 'all'):
                raise TracError, "Source type not specified or invalid"
            source = req.args.get(source_type)
            dest = req.args.get('destination')
            action = None
            if 'copy' in req.args.keys():
                action = 'copy'
            elif 'move' in req.args.keys():
                action = 'move'
            else:
                raise TracError, 'Action not specified or invalid'
                
            action_verb = {'copy':'Copied', 'move':'Moved'}[action]
            
            perm_filter = None
            if source_type == 'permission':
                in_permissions = [tuple(p.split(':', 2)) for p in req.args.getlist('perm')]
                perm_filter = lambda p: p in in_permissions
            elif source_type == 'all':
                perm_filter = lambda p: True
            
            try:
                sel_permissions = [p for p in permissions if perm_filter(p)]
                dest_env = _open_environment(dest)
                for perm in sel_permissions:
                    # revoke first in case it's already there
                    # also, go directly to the store to bypass validity checks
                    PermissionSystem(dest_env).store.revoke_permission(perm[0], perm[1])
                    PermissionSystem(dest_env).store.grant_permission(perm[0], perm[1])
                
                if action == 'move':
                    for perm in sel_permissions:
                        PermissionSystem(self.env).revoke_permission(perm[0], perm[1])
                
                req.hdf['datamover.message'] = '%s permissions %s'%(action_verb, ', '.join(["%s:%s" % (u,a) for u,a in sel_permissions]))
            except TracError, e:
                req.hdf['datamover.message'] = "An error has occured: \n"+str(e)
                self.log.warn(req.hdf['datamover.message'], exc_info=True)
        
        
        req.hdf['datamover.envs'] = envs
        req.hdf['datamover.permissions'] = permissions
        return 'datamover_permission.cs', None
