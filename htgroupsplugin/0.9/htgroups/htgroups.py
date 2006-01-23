# -*- coding: iso-8859-1 -*-

# HtGroups plugin v0.1

import os.path

from trac.core import *
from trac.perm import IPermissionGroupProvider

__all__ = ['HtGroups']

class HtGroups(Component):
    implements(IPermissionGroupProvider)

    # IPermissionGroupProvider interface method

    def get_permission_groups(self, username):
        groups = []

        if 'account-manager' in self.config:
            group_file_name = self.config.get('account-manager', 'group_file')
        else:
            group_file_name = self.config.get('htgroups', 'group_file')

        if os.path.exists(group_file_name):
            group_file = file(group_file_name)

            try:
                for group in group_file:
                    group = group.strip()
                    if group and not group.startswith('#'):
                        group_name, group_members = group.split(':', 1)
                        if username in group_members.split():
                            groups.append(group_name)
            finally:
                group_file.close()

        self.env.log.debug('groups found = ' + ','.join(groups))

        return groups
