import ldap

from trac.core import *
from trac.config import Option

from acct_mgr.api import IPasswordStore

class LDAPStore(Component):
    """An AccountManager backend to use LDAP."""
    
    server_host = Option('ldap', 'server', doc='Server to use for LDAP authentication')
    
    bind_dn = Option('ldap', 'bind_dn', doc='Template to make the bind DN')
    
    implements(IPasswordStore)
    
    def check_password(self, user, password):
        self.log.debug('LDAPAuth: Checking password for user %s', user)
        try:
            l = ldap.open(self.server_host)
            bind_name = (self.bind_dn%user).encode('utf8')
            self.log.debug('LDAPAuth: Using bind DN %s', bind_name)
            l.simple_bind_s(bind_name, password.encode('utf8'))
            return True
        except ldap.LDAPError:
            return False
