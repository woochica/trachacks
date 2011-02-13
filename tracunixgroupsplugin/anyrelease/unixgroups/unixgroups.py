# -*- coding: iso-8859-1 -*-

# UnixGroups plugin v0.1

from trac.core import *
from trac.perm import IPermissionGroupProvider
from subprocess import Popen,PIPE

__all__ = ['UnixGroups']

class UnixGroups(Component):
    implements(IPermissionGroupProvider)

    def get_permission_groups(self, username):
        groups = []
	groups_str = Popen(["groups", username], stdout=PIPE).communicate()[0]
	if groups_str.find(":")!=-1:
		groups_lst = groups_str.split(":")[1].strip()
		groups = ["@%s"% x.strip() for x in groups_lst.split()]

        self.env.log.debug('unixgroups found for %s = %s' % (username, ','.join(groups)))

        return groups
