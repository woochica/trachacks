# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>

from trac.core import implements, ExtensionPoint, Component, Interface
from trac.perm import IPermissionStore, IPermissionPolicy

__all__ = ['IPermissionUserProvider', 'UserExtensiblePermissionStore']

class IPermissionUserProvider(Interface):
    """ Provide permission actions for users """

    def get_permission_action(username):
        """ Return a list of the actions for the given username """

class UserExtensiblePermissionStore(Component):
    """ Default Permission Store extended user permission providers """
    implements(IPermissionStore, IPermissionPolicy)
    user_providers = ExtensionPoint(IPermissionUserProvider)
    
    def check_permission(self, action, username, resource, perm):
      self.log.debug("perm: checking user perms for %s to have %s on %s" % [username, action, resource])
      subjects = []
      for provider in self.group_providers:
          subjects.update(provider.get_permission_groups(username))
      if action in subjects:
        return True
      else:
        return False

    def get_user_permissions(self, username):
        """Retrieve the permissions for the given user and return them in a
        dictionary.

        The permissions are stored in the database as (username, action)
        records. There's simple support for groups by using lowercase names for
        the action column: such a record represents a group and not an actual
        permission, and declares that the user is part of that group.

        Plugins implmenting the IPermissionUserProvider can return permission
        actions based on user.  For example, return TRAC_ADMIN if a user is in
        a given LDAP group
        """        
        self.log.debug("perm: getting user perms")
        
        subjects = set([username])
        for provider in self.group_providers:
            subjects.update(provider.get_permission_groups(username))

        actions = set([])
        for provider in self.user_providers:
            actions.update(provider.get_permission_action(username))
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT username,action FROM permission")
        rows = cursor.fetchall()
        while True:
            num_users = len(subjects)
            num_actions = len(actions)
            for user, action in rows:
                if user in subjects:
                    if action.isupper() and action not in actions:
                        actions.add(action)
                    if not action.isupper() and action not in subjects:
                        # action is actually the name of the permission group
                        # here
                        subjects.add(action)
            if num_users == len(subjects) and num_actions == len(actions):
                break
              
        return list(actions)
      