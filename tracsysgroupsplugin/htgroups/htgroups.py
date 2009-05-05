# -*- coding: iso-8859-1 -*-

# HtGroups plugin v0.1

import os.path

from trac.core import *
from trac.config import *
from trac.perm import IPermissionGroupProvider

__all__ = ['HtGroups']

class HtGroups(Component):
    implements(IPermissionGroupProvider)

    #acctmgr_group_file_name = Option('account-manager', 'group_file', None,
    #    """Path of the Apache htgroups file to source (when using AccountManagerPlugin)""")
    #htgroups_group_file_name = Option('htgroups', 'group_file', None,
    #    """Path of the Apache htgroups file to source (when only using HtgroupsPlugin)""")

    # IPermissionGroupProvider interface method
    def get_permission_groups(self, username):
        groups = []

        if 'account-manager' in self.config:
            group_file_name = self.config.get('account-manager', 'group_file')
        else:
            group_file_name = self.config.get('htgroups', 'group_file')

        ## For some reason the new 0.10 Option() stuff is not working for me
        #if self.acctmgr_group_file_name is not None:
        #    group_file_name = self.acctmgr_group_file_name
        #else:
        #    group_file_name = self.htgroups_group_file_name

        if os.path.exists(group_file_name):
            group_file = file(group_file_name)

            try:
                for group in group_file:
                    group = group.strip()
                    # Ignore blank lines and lines starting with #
                    if group and not group.startswith('#'):
                        group_name, group_members = group.split(':', 1)
                        # Only include groups that the current user is a member of
                        if username in group_members.split():
                            groups.append(group_name)
            finally:
                group_file.close()

        self.env.log.debug('htgroups found for %s = %s' % (username, ','.join(groups)))

        return groups
