# Created by Noah Kantrowitz
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
import inspect

from trac.core import *
from trac.config import Option
from trac.perm import IPermissionGroupProvider, PermissionSystem, DefaultPermissionStore

from tracforge.admin.model import Project
from tracforge.admin.config import EnvironmentOption

class TracForgePermissionStore(DefaultPermissionStore):
    """Enhanced permission module to allow for central management."""

    master_env = EnvironmentOption('tracforge', 'master_path',
                                   doc='Path to master Trac')
                         
    def get_user_permissions(self, username):
        subjects = [username]
        for provider in self.group_providers:
            subjects += list(provider.get_permission_groups(username))

        actions = []
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT username,action FROM permission")
        rows = cursor.fetchall()
        master_db = self.master_env.get_db_cnx()
        master_cursor = master_db.cursor()
        master_cursor.execute("SELECT username,action FROM tracforge_permission")
        rows += master_cursor.fetchall()
        while True:
            num_users = len(subjects)
            num_actions = len(actions)
            for user, action in rows:
                if user in subjects:
                    if not action.islower() and action not in actions:
                        actions.append(action)
                    if action.islower() and action not in subjects:
                        # action is actually the name of the permission group
                        # here
                        subjects.append(action)
            if num_users == len(subjects) and num_actions == len(actions):
                break
        return [action for action in actions if not action.islower()]

    def get_all_permissions(self):
        """Return all permissions for all users.

        The permissions are returned as a list of (subject, action)
        formatted tuples."""
        perms = []
        req = self._extract_req()
        if req is None or not req.path_info == '/admin/tracforge/perm':
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT username,action FROM permission")
            perms.extend(cursor)
        
        if req is None or not req.path_info == '/admin/general/perm':
            master_db = self.master_env.get_db_cnx()
            cursor = master_db.cursor()
            cursor.execute("SELECT username,action FROM tracforge_permission")
            perms.extend(cursor)
        return perms
    
    def _extract_req(self):
        """Truly evil magic to scan for a variable called req in the stack."""
        for record in inspect.stack():
            locals = record[0].f_locals
            if 'req' in locals:
                return locals['req']
        return None
        
    def grant_permission(self, username, action):
        """Grants a user the permission to perform the specified action for the central table."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("INSERT INTO tracforge_permission VALUES (%s, %s)",
                       (username, action))
        self.log.info('Granted central permission for %s to %s' % (action, username))
        db.commit()
        
    def revoke_permission(self, username, action):
        """Revokes a users' permission to perform the specified action from the central table."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("DELETE FROM tracforge_permission WHERE username=%s AND action=%s",
                       (username, action))
        self.log.info('Revoked central permission for %s to %s' % (action, username))
        db.commit()

class TracForgeGroupsModule(Component):
    """A component to provide virtual groups based on the membership system."""
    
    master_env = EnvironmentOption('tracforge', 'master_path',
                                   doc='Path to master Trac')

    implements(IPermissionGroupProvider)

    # IPermissionGroupProvider methods
    def get_permission_groups(self, username):
        group_extn_point = PermissionSystem(self.master_env).store.group_providers
        group_providers = [x for x in group_extn_point if x.__class__.__name__ != self.__class__.__name__] # Filter out this one (recursion block)
        
        master_groups = []
        for prov in group_providers:
            master_groups += list(prov.get_permission_groups(username))

        self.log.debug('TracForgeGroupModule: Detected master groups (%s) for %s'%(', '.join([str(x) for x in master_groups]), username))

        proj = Project.by_env_path(self.master_env, self.env.path)
        access = {}
        subjects = [username] + master_groups
        for subj in subjects:
            if subj in proj:
                 access[proj.members[subj]] = True
                 
        if 'admin' in access:
            return ['admin', 'member']
        elif 'member' in access:
            return ['member']
        else:
            return []   
        
