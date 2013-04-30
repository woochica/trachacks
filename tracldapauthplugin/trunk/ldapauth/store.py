import ldap

from trac.core import (
    Component,
    implements,
    )

from trac.config import (
    BoolOption,
    Option,
    )

from acct_mgr.api import IPasswordStore


class LDAPStore(Component):
    """An AccountManager backend to use LDAP."""

    host = Option('ldap', 'host',
                  doc='Server URL to use for LDAP authentication')
    bind_dn = Option('ldap', 'bind_dn',
                     doc='Template to make the bind DN')
    use_tls = BoolOption('ldap', 'use_tls', default='false',
                         doc='enable TLS support')

    implements(IPasswordStore)

    def check_password(self, user, password):
        self.log.debug('LDAPAuth: Checking password for user %s', user)

        success = False

        try:
            conn = self._create_ldap_conn()
        except ldap.LDAPError, e:
            self.log.debug('LDAPAuth: %s', e)
            # let the authentication fall through to next store in a chain
            return None

        bind_dn = (self.bind_dn % user).encode('utf8')
        bind_pw = password.encode('utf8')

        try:
            self.log.debug('LDAPAuth: Using bind DN %s', bind_dn)
            conn.simple_bind_s(bind_dn, bind_pw)
        except ldap.INVALID_CREDENTIALS:
            self.log.debug('LDAPAuth: username or password is incorrect.')
        except ldap.LDAPError, e:
            self.log.debug('LDAPAuth: %s', e)
            # let the authentication fall through to next store in a chain
            success = None
        else:
            self.log.debug('LDAPAuth: Success Using bind DN %s', bind_dn)
            success = True

        return success

    def get_users(self):
        # TODO: investigate how to get LDAP users that successfully logged in
        return []

    def has_user(self, user):
        return False

    def _create_ldap_conn(self):
        """Creates an LDAP connection"""
        conn = ldap.initialize(self.host)
        if self.use_tls:
            conn.start_tls_s()
        return conn
