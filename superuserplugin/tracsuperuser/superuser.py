## AMB SuperUser - Give TRAC_ADMIN permissions to a configurable user
#
# Automatically gives TRAC_ADMIN permission to a defined user
# 
# [trac]
# permission_store = SuperUserPlugin
# 
# [superuser]
# superuser = admin
# wrapped_permission_store = DefaultPermissionStore

from trac.core import *
from trac.perm import IPermissionStore
from trac.config import ExtensionOption, Option

import logging


class SuperUserPlugin(Component):
    """ Adds a superuser with TRAC_ADMIN permissions """
    implements(IPermissionStore)
    
    superuser = Option('superuser', 'superuser', 'admin', 'Superuser username')
    
    store = ExtensionOption('superuser', 'wrapped_permission_store', IPermissionStore,
        'DefaultPermissionStore', """Name of the component implementing `IPermissionStore`, which is used
        for managing user and group permissions.""")
    

    def get_user_permissions(self, username):
        if username == self.superuser:
            return list(set(['TRAC_ADMIN']) | set(self.store.get_user_permissions(username)))
        else:
            return self.store.get_user_permissions(username)

    def get_users_with_permissions(self, permissions):
        return list(set([self.superuser]) | set(self.store.get_users_with_permissions(permissions)))
            
    def get_all_permissions(self):
        return self.store.get_all_permissions() + [(self.superuser, 'TRAC_ADMIN')]
        
    def grant_permission(self, username, action):
        if username == self.superuser:
            assert False, "Superuser %s can't be given any permissions" % username
        return self.store.grant_permission(username, action)
        
    def revoke_permission(self, username, action):
        if username == self.superuser:
            assert False, "Superuser %s can't be revoked any permissions" % username
        return self.store.revoke_permission(username, action)
