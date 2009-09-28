from trac.core import *
from trac.config import Option
import crypt, md5, sha, base64

from acct_mgr.api import IPasswordStore
from ldapplugin.api import *


class LdapAuthStore(Component):

    implements(IPasswordStore)
    
    def __init__(self, ldap=None, log=True):

        # looks for groups only if LDAP support is enabled
        self.enabled = self.config.getbool('ldap', 'enable')
        if not self.enabled:
            return
        self.util = LdapUtil(self.config)

        # LDAP connection
        self._ldap = ldap

        # LDAP connection config
        self._ldapcfg = {}
        for name, value in self.config.options('ldap'):
            if name in LDAP_DIRECTORY_PARAMS:
                self._ldapcfg[name] = value

        # user entry local cache
        self._cache = {}
        # max time to live for a cache entry
        self._cache_ttl = int(self.config.get('ldap', 'cache_ttl', str(15*60)))
        # max cache entries
        self._cache_size = min(25, int(self.config.get('ldap', 'cache_size', '100')))

    def has_user(self, user):
            self.log.info("checking user: %s"%user)
            return user in self.get_users()

    def get_users(self):
        self._openldap()
        #2008-03-17 change objectclass=simpleSecurityObject to object=*
        #MODIFIKEI
        #ldap_users = self._ldap.get_dn(self._ldap.basedn, '(objectclass=*)')
        self._basedn_filter = self.config.get('ldap', 'basedn_filter', 'objectClass=*')
        ldap_users = self._ldap.get_dn(self._ldap.basedn, self._basedn_filter)
		
        self.log.info("ldap_users: %s"%(ldap_users))
        users = []
        for user in ldap_users:
            m = re.match('uid=([^,]+)', user)
            if m:
                users.append(m.group(1))
        return users

    def set_password(self, user, password):
        user = user.encode('utf-8')
        password = password.encode('utf-8')
        md5_password = "{MD5}" + base64.encodestring(md5.new(password).digest()).rstrip()

        userdn = self._get_userdn(user)
        p = self._ldap.get_attribute(userdn, 'userPassword')
        
        self._ldap.add_attribute(userdn, 'userPassword', md5_password)
        self._ldap.delete_attribute(userdn, 'userPassword', p[0])

    def check_password(self, user, password, log=True):
        userdn = self._get_userdn(user)
        if userdn is False:
                return False

        password = password.encode('utf-8')
        p = self._ldap.get_attribute(userdn, 'userPassword')
        stored = p[0]
        m = re.match('^({[^}]+})', stored)
        if m:
            mech = m.group(0)
            if (mech == '{MD5}') or (mech == '{md5}'):
                password = mech + base64.encodestring(md5.new(password).digest()).rstrip()
            elif (mech == '{CRYPT}') or (mech == '{crypt}'):
                password = mech + crypt.crypt(password, stored[7:])
            elif (mech == '{SSHA}') or (mech == '{ssha}'):
                challenge_bytes = base64.decodestring(stored[6:])
                digest = challenge_bytes[:20]
                salt = challenge_bytes[20:]
                hr = sha.new(password)
                hr.update(salt)
                password = digest
                stored = hr.digest()
        if stored == password: 
            for attr in ('name', 'email'): 
                fieldname = str(self.config.get('ldap', attr )) 
                self.env.log.debug('LDAPstore : Getting %s for %s' % ( fieldname , attr )) 
                value = self._ldap.get_attribute(userdn, fieldname) 
                if not value: 
                    continue 
                value = unicode(value[0], 'utf-8') 
                self.env.log.debug('LDAPstore : Got value %s for attribute %s' % ( value , attr )) 
                db = self.env.get_db_cnx() 
                cursor = db.cursor()
                cursor.execute("SELECT * from session_attribute WHERE sid=%s", (user))
                db.commit()
                if not cursor.rowcount:
                    cursor.execute("UPDATE session_attribute SET value=%s " 
                                   "WHERE name=%s AND sid=%s AND authenticated=1", 
                                   (value, attr, user)) 
                    db.commit()
                    if not cursor.rowcount:
                        cursor.execute("INSERT INTO session_attribute " 
                                       "(sid,authenticated,name,value) " 
                                       "VALUES (%s,1,%s,%s)", 
                                       (user, attr, value)) 
                        db.commit() 
            return True 
        return False 

    def _openldap(self):
        """Open a new connection to the LDAP directory"""
        if getattr(self, '_ldap') is None: 
            bind = self.config.getbool('ldap', 'store_bind')
            self._ldap = LdapConnection(self.log, bind, **self._ldapcfg)
        self._ldap._open()

    def _get_userdn(self, user):
        self._openldap()
        #2008-03-17 yh: change objectclass=simpleSecurityObject to object=*
        #ldap_users = self._ldap.get_dn(self._ldap.basedn, '(objectclass=*)')
        self._basedn_filter = self.config.get('ldap', 'basedn_filter', 'objectClass=*')
        ldap_users = self._ldap.get_dn(self._ldap.basedn, self._basedn_filter)

        for u in ldap_users:
            m = re.match('uid=([^,]+)', u)
            if m:
                if user == m.group(1):
                    return u
        return False
