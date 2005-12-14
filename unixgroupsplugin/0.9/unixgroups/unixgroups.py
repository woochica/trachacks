# UnixGroups plugin v1.0

from pwd import *
from grp import *
from trac.core import *
from trac.perm import IPermissionGroupProvider

class UnixGroups(Component):
    implements(IPermissionGroupProvider)

    # IPermissionGroupProvider methods
    def get_permission_groups(self, username):
        try:
            maingroup = getgrgid(getpwnam(username).pw_gid).gr_name
        except KeyError:
            return []
        othergroups = [g.gr_name for g in getgrall() if username in g.gr_mem]
        return [maingroup] + othergroups
