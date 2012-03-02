# To change this template, choose Tools | Templates
# and open the template in the editor.

import ldap

from trac.core import *
from trac.config import *
from acct_mgr.api import IPasswordStore

class LDAPAuthNStore (Component):
    server = Option('ldap', 'server', 'ldap://localhost:389',doc='Server to use for LDAP authentication')
    root_dn = Option('ldap', 'root_dn',doc='This field specifies the Root subtree')
    user_searchbase = Option('ldap', 'user_searchbase', 'ou=people')
    user_searchfilter = Option('ldap', 'user_searchfilter', 'uid=%s', doc='This field determines the filter to be run to identify the user record. The query is almost always "uid=%s"')
    anonymous_bind = BoolOption('ldap', 'anonymous_bind', True, doc='If server accepts anonymous bind')
    bind_dn = Option('ldap', 'bind_dn', doc='If the server does not accept anonymous bind, then it requires a bind_dn')
    bind_passwd = Option('ldap', 'bind_passwd')

    implements(IPasswordStore)

    def check_password(self, user, password):
        con = self.init_connection()

        base = self.user_searchbase + ',' + self.root_dn
        filter = self.user_searchfilter % user
        
        ''' require nested "try:" in order to support python2.4 '''
        try:
            try:
                resp = con.search_s(base, ldap.SCOPE_SUBTREE, filter, ['dn'])

                if not len(resp) :
                    return None

                resp = con.simple_bind_s(resp[0][0], password)
                return True
            except ldap.INVALID_CREDENTIALS:
                self.log.debug('bad credentials, user %s not authenticated.', user)
                return False
        finally:
            con.unbind()


    def get_users(self):
        con = self.init_connection()

        base = self.user_searchbase + ',' + self.root_dn
        filter = 'objectclass=person'
        
        resp = None
        
        try:
            resp = con.search_s(base, ldap.SCOPE_SUBTREE, filter, ['dn','uid'])
        finally:
            con.unbind()
        
        for entry in resp:
            if entry[1]['uid'][0]:
                yield entry[1]['uid'][0]
    '''
    def set_password(self, user, password):
        con = self.init_connection()
        con.passwd_s(dn, password)
         
        self.log.debug('set password for %s current %s', user, password)
    '''
        

    def init_connection(self):
        connection = ldap.initialize(self.server)

        if self.server.startswith('ldaps'):
            connection.start_tls_s()

        if not self.anonymous_bind:
            resp = connection.simple_bind_s(self.bind_dn, self.bind_passwd)

        return connection
