# Created by Noah Kantrowitz on 2007-05-27.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.core import *
from trac.perm import IPermissionRequestor

class ModAuthAcctMgrModule(Component):
    """Some utility permissions for mod_auth_acctmgr."""

    implements(IPermissionRequestor)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'SVN_READ'
        yield 'SVN_WRITE'
