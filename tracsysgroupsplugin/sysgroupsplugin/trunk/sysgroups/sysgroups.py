# -*- coding: iso-8859-1 -*-

# SysGroups plugin v0.1

import pwd, grp

from trac.core import *
from trac.config import *
from trac.perm import IPermissionGroupProvider


__all__ = ['SysGroups']

class SysGroups(Component):
    implements(IPermissionGroupProvider)

    # IPermissionGroupProvider interface method
    def get_permission_groups(self, username):
        groups = []

        for p in grp.getgrall():
            if username in p[3] : groups.append(p[0]) 

        self.env.log.debug('sysgroups found for %s = %s' % (username, ','.join(groups)))

        return groups
