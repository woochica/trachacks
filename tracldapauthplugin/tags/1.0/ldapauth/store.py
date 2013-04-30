import ldap

from trac.core import *
from trac.config import BoolOption
from trac.config import Option

from acct_mgr.api import IPasswordStore

class LDAPStore(Component):
    """An AccountManager backend to use LDAP."""

    host = Option('ldap', 'host', doc='Server to use for LDAP authentication')    
    bind_dn = Option('ldap', 'bind_dn', doc='Template to make the bind DN')
    use_tls = BoolOption('ldap', 'use_tls', default='false', doc='enable TLS support') 

    implements(IPasswordStore)

    def check_password(self, user, password):
        self.log.debug('LDAPAuth: Checking password for user %s', user)
        try:
            l = ldap.open(self.host)
            if self.use_tls:
                l.start_tls_s()
            bind_name = (self.bind_dn%user).encode('utf8')
            self.log.debug('LDAPAuth: Using bind DN %s', bind_name)
            l.simple_bind_s(bind_name, password.encode('utf8'))
            return True
        except ldap.LDAPError:
            return None
