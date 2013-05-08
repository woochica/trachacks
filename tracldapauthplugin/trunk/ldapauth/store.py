import ldap
import traceback

from trac.core import (
    Component,
    implements,
    )

from trac.config import (
    BoolOption,
    ChoiceOption,
    Option,
    )

from acct_mgr.api import IPasswordStore

SEARCH_SCOPES = ('base', 'onelevel', 'subtree')

PASSWORDSTORE_SUCCESS = True
PASSWORDSTORE_FAILURE = False
PASSWORDSTORE_FALLTHROUGH = None


class LDAPStore(Component):
    """An AccountManager backend to use LDAP."""

    host_url = Option('ldap', 'host_url',
                      doc='Server URL to use for LDAP authentication')
    base_dn = Option('ldap', 'base_dn', doc='The user search base')
    bind_user = Option('ldap', 'bind_user', doc='LDAP user for searching')
    bind_password = Option('ldap', 'bind_password', doc='LDAP user password')
    search_scope = ChoiceOption('ldap', 'search_scope', SEARCH_SCOPES,
                                doc='The ldap search scope: base, onelevel or '
                                    'subtree')
    search_filter = Option('ldap', 'search_filter',
                           default='(&(objectClass=user)(sAMAccountName=%s))',
                           doc='The ldap search filter template where %%s is '
                               'replace with the username')

    implements(IPasswordStore)

    def check_password(self, user, password):
        self.log.debug('LDAPAuth: Checking password for user %s', user)

        conn = None
        try:
            conn = self._create_ldap_conn()
            if conn is not None and self._authenticate(conn, self.bind_user,
                                                       self.bind_password):
                bind_cn = self._search_user(conn, user)
                if bind_cn is not None and self._authenticate(conn, bind_cn,
                                                              password):
                    return PASSWORDSTORE_SUCCESS
                else:
                    return PASSWORDSTORE_FAILURE
            else:
                return PASSWORDSTORE_FALLTHROUGH
        except Exception:
            self.log.debug('LDAPAuth: Unexpected error: %s',
                           traceback.format_exc())
        finally:
            if conn is not None:
                conn.unbind_s()

        return PASSWORDSTORE_FALLTHROUGH

    def get_users(self):
        # TODO: investigate how to get LDAP users that successfully logged in
        return []

    def has_user(self, user):
        return False

    def _create_ldap_conn(self):
        """Creates an LDAP connection"""
        self.log.debug('LDAPAuth: Initializing LDAP connection for %s',
                       self.host_url)
        conn = None
        try:
            conn = ldap.initialize(self.host_url)
            if self._should_use_tls():
                self.log.debug('LDAPAuth: starting TLS')
                conn.start_tls_s()
        except ldap.LDAPError, e:
            self.log.debug('LDAPAuth: Could not create connection: %s', e)

        return conn

    def _authenticate(self, conn, who, cred):
        self.log.debug('LDAPAuth: Authenticating using %s', who)

        success = False

        try:
            conn.simple_bind_s(who, cred)
        except ldap.INVALID_CREDENTIALS:
            self.log.debug('LDAPAuth: username "%s" or password is incorrect.',
                           who)
        except ldap.LDAPError, e:
            self.log.debug('LDAPAuth: %s', e)
        else:
            self.log.debug('LDAPAuth: Success authenticating %s', who)
            success = True

        return success

    def _search_user(self, conn, user):
        bind_cn = None
        users_found = conn.search_s(self.base_dn, self._get_search_scope(),
                                    self.search_filter % user)
        if users_found is not None and len(users_found) == 1:
            self.log.debug('LDAPAuth: bind user %s exists', user)
            bind_cn = users_found[0][0]
        return bind_cn

    def _should_use_tls(self):
        return self.host_url.startswith('ldaps')

    def _get_search_scope(self):
        if self.search_scope not in SEARCH_SCOPES:
            self.log.debug('LDAPAuth: search scope %s is not supported',
                           self.search_scope)
            self.search_scope = SEARCH_SCOPES[0]
        self.log.debug('LDAPAuth: using search scope %s', self.search_scope)
        return getattr(ldap, 'SCOPE_%s' % self.search_scope.upper())


