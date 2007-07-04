# Copyright David Abrahams 2007. Distributed under the Boost
# Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

from trac.core import *
from trac.config import ExtensionOption
from trac.perm import IPermissionGroupProvider

print 'loading userlist'

__all__ = ['IUserList', 'IRoleProvider',
           'DefaultUserList']

class IUserList(Interface):
    """Interface for components that provides sequences of usernames (sids)."""
    
    def get_all_users(self):
        """Return a sequence of all users in the system."""

class IRoleProvider(Interface):
    """Interface for extension points that provide sequences of usernames (sids)."""
    
    def get_roles(self):
        """Return a sequence of users known to this provider."""
    

class SessionRoleProvider(Component):
    """Provides the sequence of users who have a record in the session table."""
    implements(IRoleProvider)

    def get_roles(self):
        return [username for username,name,email in self.env.get_known_users()]

class DefaultPermissionRoleProvider(Component):
    """Provides the sequence of users known to the default permission system."""
    implements(IRoleProvider)

    def get_roles(self):
        cursor = self.env.get_db_cnx().cursor()
        roles = set()
        groups = set(['anonymous', 'authenticated'])
        cursor.execute("SELECT username,action FROM permission")
        
        for role,action in cursor:
            roles.add(role)
            if not action.isupper():
                groups.add(action)

        print 'DefaultPermissionRoleProvider: returning ', roles-groups
        return roles - groups
        
class DefaultUserList(Component):
    """The default implementation of a central place one goes to get a list of
       all users in the system."""
    
    implements(IUserList)
    
    role_providers = ExtensionPoint(IRoleProvider)
    group_providers = ExtensionPoint(IPermissionGroupProvider)
    
    def get_all_users(self):

        def as_set(s):
            if isinstance(s,set):
                return s
            return set(s)
            
        roles = set()
        for p in self.role_providers:
            roles |= as_set(p.get_roles())

        # The following is horribly inefficient.  However, for restrict_owner
        # (which uses get_users_with_permissions) it is essential to eliminate
        # groups from the list of roles, and right now we don't have a better
        # way.
        potential_users = set(roles)
        groups = set()
        for p in self.group_providers:
            print 'group provider: ', type(p)
            for u in potential_users:
                print 'groups of', u,
                print '=', p.get_permission_groups(u)
                groups |= as_set(p.get_permission_groups(u))
            
        return potential_users - groups

class UserManager(Component):
    """The central place one goes to get a list of all users in the system."""
    
    implements(IUserList)

    implementation = ExtensionOption('trac', 'user_list', IUserList,
                            'DefaultUserList',
        """Name of the component implementing `IUserList`, which is used
        to collect the list of known users.""")

    def get_all_users(self):
        return self.implementation.get_all_users()
    
