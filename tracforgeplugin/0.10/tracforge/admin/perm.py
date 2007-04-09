from trac.core import *
from trac.config import Option
from trac.perm import IPermissionGroupProvider, PermissionSystem, DefaultPermissionStore
from trac.env import Environment

from model import Project
from config import EnvironmentOption

import inspect

class TracForgePermissionModule(DefaultPermissionStore):
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
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT username,action FROM permission")
        rows = cursor.fetchall()
        req = self._extract_req()
        if req is not None and not req.path_info.startswith('/admin/general/perm'):
            master_db = self.master_env.get_db_cnx()
            master_cursor = master_db.cursor()
            master_cursor.execute("SELECT username,action FROM tracforge_permission")
            rows += master_cursor.fetchall()
        return [(row[0], row[1]) for row in rows]

    def _extract_req(self):
        """Truly evil magic to scan for a variable called req in the stack."""
        for record in inspect.stack():
            locals = record[0].f_locals
            if 'req' in locals:
                return locals['req']
        return None

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
        
