# Created by Noah Kantrowitz
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
from trac.core import *
from trac.admin.web_ui import PermissionAdminPanel
from trac.util.translation import _

class TracForgePermissionAdminPage(PermissionAdminPanel):

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if 'TRACFORGE_ADMIN' in req.perm:
            yield 'tracforge', _('TracForge'), 'perm', _('Permissions')
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ()