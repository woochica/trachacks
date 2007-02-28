from trac.core import *
from trac.perm import IPermissionGroupProvider
from trac.versioncontrol.svn_authz import SubversionAuthorizer, \
                                          RealSubversionAuthorizer

class SvnAuthzGroupProvider(Component):
    implements(IPermissionGroupProvider)

    def get_permission_groups(self, username):
        authz = SubversionAuthorizer(self.env, None, username)
        if isinstance(authz, RealSubversionAuthorizer):
            return authz._groups()
        else:
            return []
