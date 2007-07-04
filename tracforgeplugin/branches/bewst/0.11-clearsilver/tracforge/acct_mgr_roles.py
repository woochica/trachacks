# Copyright David Abrahams 2007. Distributed under the Boost
# Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
from trac.core import *
from userlist import *
from acct_mgr.api import AccountManager

print 'loading acct_mgr_userlist'

class AccountManagerRoleProvider(Component):
    """Provides the sequence of users known to the AccountManager plugin."""
    implements(IRoleProvider)

    def get_roles(self):
        return AccountManager(self.env).get_users()

