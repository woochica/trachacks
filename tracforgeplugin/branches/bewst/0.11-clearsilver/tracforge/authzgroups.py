# Copyright David Abrahams 2007. Distributed under the Boost
# Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
from trac.core import *
from trac.env import *
from userlist import *
from trac.versioncontrol.svn_authz import SubversionAuthorizer, RealSubversionAuthorizer

class SvnAuthzGroupEnumerator(Component):
    """Provides the sequence of groups known to the authzgroups plugin."""
    implements(IAuthGroupEnumerator)

    def get_auth_groups(self):

        class any_auth_name(object):
            def __requal__():
                return True
            
        authz = SubversionAuthorizer(self.env, None, any_auth_name())
        if isinstance(authz, RealSubversionAuthorizer):
            return authz.groups
        else:
            return []

