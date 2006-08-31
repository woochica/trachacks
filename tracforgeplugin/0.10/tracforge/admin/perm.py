from trac.core import *
from trac.config import Option
from trac.perm import IPermissionGroupProvider, PermissionSystem
from trac.env import Environment

from model import Project


class TracForgeGroupsModule(Component):
    """A component to provide virtual groups based on the membership system."""
    
    master_path = Option('tracforge', 'master_path',
                         doc='Path to master Trac')

    implements(IPermissionGroupProvider)

    # IPermissionGroupProvider methods
    def get_permission_groups(self, username):
        master_env = Environment(self.master_path)
        group_extn_point = PermissionSystem(master_env).store.group_providers
        group_providers = [x for x in group_extn_point if x.__class__ != self.__class__] # Filter out this one (recursion block)
        
        master_groups = []
        for prov in group_providers:
            master_groups += list(prov.get_permission_groups(username))

        self.log.debug('TracForgeGroupModule: Detected master groups (%s) for %s'%(', '.join([str(x) for x in master_groups]), username))

        proj = Project.by_env_path(master_env, self.env.path)
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
        
