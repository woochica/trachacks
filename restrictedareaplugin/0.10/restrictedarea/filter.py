from trac.core import *
from trac.config import ListOption
from trac.perm import IPermissionRequestor, PermissionError
from trac.web.api import IRequestFilter, HTTPForbidden
from trac.util.text import to_unicode

__all__ = ['RestrictedAreaFilter']

class RestrictedAreaFilter(Component):
    """Request filter allowing only privileged users to access certain pages."""
    
    __action_name = 'RESTRICTED_AREA_ACCESS'
    
    paths = ListOption('restrictedarea', 'paths', default='/wiki/restricted',
                doc='Paths that allow only users with the `RESTRICTED_AREA_ACCESS` privileges.')
    
    implements(IRequestFilter, IPermissionRequestor)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return [self.__action_name]

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        for path in self.paths:
            if req.path_info.startswith(path) and not req.perm.has_permission(self.__action_name):
                raise HTTPForbidden(to_unicode(PermissionError(self.__action_name)))
        return handler

    def post_process_request(self, req, template, content_type):
        return template, content_type
