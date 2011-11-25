'''
XMail Permission Modul

@author: stefan.ernst
'''

import re
from trac.core import * 

from trac.perm import IPermissionRequestor,PermissionSystem

#===========================================================================
# accepted permissions for this plugin
#===========================================================================
permissionList = ("TRAC_ADMIN", "XMAIL_ADMIN")
    

#===========================================================================
# Method returns true, if the given user from the request object meets
# the required demands
#===========================================================================
def checkPermissions(self,req):
        for permission in permissionList:
            if permission in PermissionSystem(self.env).get_user_permissions(req.authname):
                return True
        return False
    
    
#===========================================================================
# Class to publish an additional Permission Type
#===========================================================================    
class XMailPermission(Component):
    implements(IPermissionRequestor)
    """ publicise permission XMAIL_ADMIN """

    definedPermissions = ("XMAIL_ADMIN")
    #IPermissionRequestor
    def get_permission_actions(self):
        yield self.definedPermissions
        

       
    
        