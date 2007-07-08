# Copyright David Abrahams 2007. Distributed under the Boost
# Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

from trac.core import *
from trac.config import ExtensionOption
from trac.perm import IPermissionGroupProvider

__all__ = ['IRoleManager', 'IRoleProvider',
           'DefaultRoleManager', 'IAuthGroupEnumerator' ]

class IRoleManager(Interface):
    """Interface for components that provides sequences of roles,
    which could be user names or group names."""
    
    def get_all_roles(self):
        """Return a sequence of all roles in the system."""

    def get_all_users(self):
        """Return a sequence of all user roles in the system."""

    def get_all_groups(self):
        """Return a sequence of all group roles in the system."""

class IRoleProvider(Interface):
    """Interface for extension points that provide sequences of roles,
    which could be user names or group names."""
    
    def get_roles(self):
        """Return a sequence of users known to this provider."""
    
class IAuthGroupEnumerator(Interface):
    """Interface for extension points that enumerate roles that are not usernames."""
    
    def get_auth_groups(self):
        """Return a sequence of groups known to this enumerator."""

class SessionRoleProvider(Component):
    """Provides the sequence of users who have a record in the session table."""
    implements(IRoleProvider)

    def get_roles(self):
        return (username for username,name,email in self.env.get_known_users())

class DefaultPermissionRoleProvider(Component):
    """Provides the roles and groups known to the default permission system."""
    implements(IRoleProvider)
    implements(IAuthGroupEnumerator)

    def get_roles(self):
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("SELECT username,action FROM permission")
        
        # for this particular application, adding the auth_groups here is
        # wasteful because we know they will eventually be subtracted.  However,
        # we're trying to make IRoleProvider a general interface, so we return
        # *all* known roles.
        return set(role for role,action in cursor) | self.get_auth_groups()
        
    def get_auth_groups(self):
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("SELECT username,action FROM permission")
        return set(['anonymous', 'authenticated']) | set(
            action for role,action in cursor if not action.isupper()
            )
        
class DefaultRoleManager(Component):
    """The default implementation of a central place one goes to get a list of
       all users in the system."""
    
    implements(IRoleManager)
    
    role_providers = ExtensionPoint(IRoleProvider)
    group_enumerators = ExtensionPoint(IAuthGroupEnumerator)

    @staticmethod
    def as_set(s):
        if isinstance(s,set):
            return s
        return set(s)

    def get_all_users(self):
        return self.get_all_roles() - self.get_all_groups()

    def get_all_roles(self):
        return reduce(
            lambda x,y:x|y,
            (self.as_set(p.get_roles()) for p in self.role_providers))
    
    def get_all_groups(self):
        return reduce(
            lambda x,y:x|y,
            (self.as_set(p.get_auth_groups()) for p in self.group_enumerators))

class UserManager(Component):
    """The central place one goes to get a list of all users in the system."""
    
    implements(IRoleManager)

    implementation = ExtensionOption('trac', 'user_list', IRoleManager,
                            'DefaultRoleManager',
        """Name of the component implementing `IRoleManager`, which is used
        to collect the list of known users.""")

    def get_all_users(self):
        return self.implementation.get_all_users()
    
    def get_all_roles(self):
        return self.implementation.get_all_roles()
    
    def get_all_groups(self):
        return self.implementation.get_all_groups()
    
