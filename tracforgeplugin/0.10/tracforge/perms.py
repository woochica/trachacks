# Tracforge global permissions

from trac.core import *
from trac.perm import IPermissionRequestor

class TracforgePermissions(Component):
    """Implements permissions for TracForge."""
    
    implements(IPermissionRequestor)
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        actions = ['TRACFORGE_CREATE']
        return actions + [('TRACFORGE_ADMIN', actions)]
