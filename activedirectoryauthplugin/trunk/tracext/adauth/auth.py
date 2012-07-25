# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>
# Extended: Branson Matheson <branson.matheson@nasa.gov>

from trac.core import *
from trac.config import Option
from trac.util.text import to_unicode

import ldap
import time
import md5
import cPickle

from acct_mgr.api import IPasswordStore
from trac.perm import IPermissionGroupProvider
from tracext.adauth.api import IPermissionUserProvider

GROUP_PREFIX = '@'

__all__ = ['ADAuthStore']

class ADAuthStore(Component):
    """AD Password Store for Account Manager """

    implements(IPasswordStore, IPermissionUserProvider, IPermissionGroupProvider)

    ads = Option('account-manager', 'ad_server', 'localhost', 'Address of the Active Directory Server')
    charset = Option('account-manager', 'ad_charset', 'utf-8', 'Text encoding used by the Active Directory Server') 
    base_dn = Option('account-manager', 'base_dn', None, 'Base DN used for account searches')
    bind_dn = Option('account-manager', 'bind_dn', None, 'DN used to bind to Active Directory')
    bind_pw = Option('account-manager', 'bind_passwd', None, 'Password used when binding to Active Directory')
    auth_group = Option('account-manager', 'auth_group', None, 'DN of group containing valid users. If None, any AD user is valid')
    admin_group = Option('account-manager', 'admin_group', None, 'DN of group containing TRAC_ADMIN users')
    show_disabled_users = Option('account-manager', 'show_disabled_users', 1, 'Show Disabled Users')
    ldap_timeout = Option('account-manager', 'ldap_timeout', 5, 'ldap response timeout in seconds')
    cache_ttl = Option('account-manager', 'cache_timeout', 60, 'cache timeout in seconds')
    memcache_size = Option('account-manager', 'memcache_size', 400, 'size of memcache in entries, zero to disable')
    memcache_prune_percent = Option('account-manager', 'memcache_prune_percent', 5, 'percent of entries to prune')
    memcache_size_warn = Option('account-manager', 'memcache_size_warn', 300, 'warning message for cache pruning in seconds')
    
    def __init__(self,ldap=None):
        #-- cache my ldap handle
        self._ldap = ldap
        #-- have a memory cache
        self._cache = {}

    # IPasswordStore
    def config_key(self):
        """Deprecated"""

    def get_users(self, populate_session=True):
      """Grab a list of users from Active Directory"""
      #-- check memcache
      userlist = self._cache_get('allusers')
      if userlist:
        return userlist
      
      if self.show_disabled_users:
        filter = "(objectClass=person)",
      else:
        filter = "(&(objectClass=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))",
        
      #-- cache miss.. goto ad
      if self.auth_group:
          userinfo = self.expand_group_users(self.auth_group)
      else:
          users = self._ad_search(self.base_dn, ldap.SCOPE_SUBTREE, filter,
                                    ['sAMAccountName', 'mail',
                                     'proxyAddresses', 'displayName'])
          userinfo = [self._get_userinfo(u[1]) for u in users 
                      if is_valid(u[1])]
          
      if populate_session and userinfo:
          self._populate_user_session(userinfo)
      userlist = list(set([u[0] for u in userinfo]))
      if userlist: 
          self.log.debug('userlist: %s ' % ",".join(userlist))
      
      self._cache_set('allusers', userlist)
      return userlist

    def expand_group_users(self, group_dn):
      #-- check memcache
      users = self._cache_get(group_dn)
      if users:
         return users
              
      groupfilter = '(%s)' % (group_dn.split(',')[0])
      """Given a group name, enumerate all members"""
      g = self._ad_search(self.base_dn, ldap.SCOPE_SUBTREE, groupfilter, ['member'])
      if g and g[0][1].has_key('member'):
          users = []
          for m in g[0][1]['member']:
              m_filter = '(%s)' % (m.split(',')[0])
              e = self._cache_get(m_filter)
              if not e:
                  e = self._ad_search(self.base_dn, ldap.SCOPE_SUBTREE, m_filter)
                  self._cache_set(m_filter,e)
              if e:
                  if 'person' in e[0][1]['objectClass']:
                      users.append(self._get_userinfo(e[0][1]))
                  elif 'group' in e[0][1]['objectClass']:
                      users.extend(self.expand_group_users(e[0][0].decode(self.charset)))
                  else:
                      self.log.debug('The group member (%s) is neither a group nor a person' % e[0][0])
              else:
                  self.log.debug('Unable to find user listed in group: %s' % str(m))
                  self.log.debug('This is very strange and you should probably check '
                                 'the consistency of your LDAP directory.' % str(m))
          
          self._cache_set(group_dn, users)
          return users
      else:
          self.log.debug('Unable to find any members of the group %s' % group_dn)
          self._cache_set(group_dn, [])
          return []

    def has_user(self, user):
      hasuser = self._cache_get('hasuser: %s' % user)
      if hasuser:
          return hasuser
      users = self.get_users()
      hasuser = user.lower() in users
      self._cache_set('hasuser: %s' % user, hasuser)
      return hasuser

    def check_password(self, user, password):
        """Checks the password against LDAP"""
        dn =  self._cache_get(':dn: %s' % user)
        if not dn:
            dn = self._get_user_dn(user)
            self._cache_set('dn: %s' % user, dn)
        success = None
        msg = "User Login: %s" % str(user)
        if dn:
            success = self._bind_ad(dn, password) or False
        if success:
            msg += " Password Verified"
            success = True
        elif success is False:
            msg += " Password Failed"
        else:
            msg += " does not exist in AD, deferring authentication"
        self.log.debug(msg)
        return success

    def delete_user(self, user):
        """Can't delete from LDAP"""
        self.log.debug("Can not delete users from Active Directory")
        return False

    # IPermissionUserProvider
    def get_permission_action(self, username):
        """ Return TRAC_ADMIN if user is in the self.admin_group """

        if self.admin_group:
            users = [u[0] for u in self.expand_group_users(self.admin_group)]
            if username in users:
                self.log.debug("User is in %", self.admin_group)
                return ['TRAC_ADMIN']
        return []
      
    # IPermissionGroupProvider
    def get_permission_groups(self, username):
        """Return a list of names of the groups that the user with the 
        specified name is a member of."""
        
        groups = self._cache_get(username)
        if groups:
          return groups
        
        # get dn
        dn = self._get_user_dn(username)
        if dn: 
            # retrieves the user groups from LDAP
            groups = self._get_user_groups(dn)
            if groups:
                self.env.log.debug('%s has groups: %s' % (username, ','.join(groups)))
            else:
                self.env.log.debug('username %s (%s) has no groups', username, dn)
                
            self._cache_set(username, groups)
            return groups
                
        else:
            self.log.debug("username: %s has no dn." % username)
            return []
      
    # Internal methods

    def _bind_ad(self, user_dn=None, passwd=None):
        user = user_dn or self.bind_dn
        password = passwd or self.bind_pw

        if self._ldap:
            return self._ldap
            
        if not self.ads.lower().startswith('ldap://'):
            ads = 'ldap://%s' % self.ads
        else:
            ads = self.ads

        # setup the ldap connection.. init does NOT attempt a connection, but search does.
        self._ldap = ldap.ldapobject.ReconnectLDAPObject(ads, retry_max=5)

        if not user:
            raise TracError('The bind_dn ini option must be set')
        if not password:
            raise TracError('The bind_pw ini option must be set')

        
        self.log.debug('Bindng to %s as %s' % (ads, user))
        try:
            self._ldap.simple_bind_s(user, password)
        except Exception, e:
            self.log.debug('Unable to bind to %s : %s' % ads, exc_info=e)
            return None 
          
        self.log.debug('Bound to %s as %s' % (ads, user))
          
        #-- allow restarting
        self._ldap.set_option(ldap.OPT_RESTART, 1)
        self._ldap.set_option(ldap.OPT_TIMEOUT, int(self.ldap_timeout))
        
        return self._ldap
   
   ### searches
    def _get_user_dn(self, user):
        """ Get users dn """
        if self.has_user(user):
          
            dn = self._cache_get('dn: %s' % user)
            if dn:
              return dn
            
            try:
               u = self._ad_search(self.base_dn, ldap.SCOPE_SUBTREE, "(&(objectClass=person)(sAMAccountName=%s))" % user, ['sAMAccountName'])
            except Exception, e:
               self.log.debug('user not found: %s' % user, exc_info=e)
               dn = None
                  
            dn = u[0][0]
            self._cache_set('dn: %s' % user, dn)
            return dn
          
        return None
      
    def _get_user_groups(self, dn):
        """Returns a list of all groups a user belongs to"""
        
        groups = self._cache_get('groups: %s' % dn)
        if groups:
          return groups
        
        groups = []
        ldapgroups = self._ad_search(self.base_dn, ldap.SCOPE_SUBTREE, '(&(objectClass=group)(member=%s))' % dn, ["sAMAccountName"])
              
        # append and recurse 
        for group in ldapgroups:
            groupname = GROUP_PREFIX + group[1]['sAMAccountName'][0].lower().replace(' ','_')
            if groupname not in groups:
                groups.append(groupname)
                subgroups = self._get_user_groups(group[0])
                if subgroups: 
                    for subgroup in subgroups:
                        if subgroup not in groups:
                            groups.append(subgroup)
                               
        if groups:
            self.log.debug('user:%s groups: %s' % (dn, ",".join(groups)))
        self._cache_set('groups: %s' % dn, groups)
        return groups
              

    def _get_userinfo(self, attrs):
        """ Extract the userinfo tuple from the LDAP search result """
        username = attrs['sAMAccountName'][0].lower()
        displayname = attrs.get('displayName', [''])[0]
        email = ''
        if 'mail' in attrs:
            email = attrs['mail'][0].lower()
        elif 'proxyAddresses' in attrs:
            for e in attrs['proxyAddresses']:
                if e.startswith('SMTP:'):
                    email = e[5:]
                continue
        return (username, displayname, email)

    def _populate_user_session(self, userinfo):
        """ Create user session entries and populate email and last visit """

        # Kind of ugly.  First try to insert a new session record.  If it
        # fails, don't worry, means it's already there.  Second, insert the
        # email address session attribute.  If it fails, don't worry, it's
        # already there.
        db = self.env.get_db_cnx()
        lastvisit = 0
        for uname, displayname, email in userinfo:
            try:
                cur = cnx.cursor()
                cur.execute('INSERT INTO session (sid, authenticated, '
                            'last_visit) VALUES (%s, 1, %s)',
                            (uname, lastvisit))
                db.commit()
            except:
                db.rollback()
            if email:
                try:
                    cur = cnx.cursor()
                    cur.execute("INSERT INTO session_attribute"
                                "    (sid, authenticated, name, value)"
                                " VALUES (%s, 1, 'email', %s)",
                                (uname, to_unicode(email)))
                    db.commit()
                except:
                    db.rollback()
            if displayname:
                try:
                    cur = cnx.cursor()
                    cur.execute("INSERT INTO session_attribute"
                                "    (sid, authenticated, name, value)"
                                " VALUES (%s, 1, 'name', %s)",
                                (uname, to_unicode(displayname)))
                    db.commit()
                except:
                    db.rollback()
            continue
        db.close()
        
    def _cache_get(self, key=None):
        """Get an item from memory cache"""
        if not self.memcache_size:
          return None;
        
        now = time.time()
            
        if key in self._cache:
            lut, data = self._cache[key]            
            if lut+int(self.cache_ttl) >= now:
              self.env.log.debug('memcache hit for %s' % key)
              return data
            else: 
             del self._cache[key] 
        return None
    
    def _cache_set(self, key=None, data=None, cache_time=None):
      if not self.memcache_size:
        return None
      #-- figure out time
      now = time.time()
      if not cache_time:
        cache_time = now
         
      #-- prune if we need to 
      if len(self._cache) > int(self.memcache_size):
        #-- warn if too frequent
        if 'last_prune' in self._cache:
          last_prune, data = self._cache['last_prune']
          if last_prune + self.memcache_size_warn > now:
            self.env.log.info('pruning memcache in less than %d seconds, you might increase memcache_size.' % int(self.memcache_size_warn) )
                
        self.env.log.debug('pruning memcache by %d: (current: %d > max: %d )' %( self.memcache_prune_percent, len(self._cache), int(self.memcache_size)))
        cache_keys = self._cache.keys()
        cache_keys.sort(lambda x,y: cmp(self._cache[x][0], 
                                           self._cache[y][0]))
        # discards the 10% oldest
        old_keys = cache_keys[:(int(self.memcache_prune_percent)*int(self.memcache_size))/100]
        for k in old_keys:
           del self._cache[k]
        self._cache['last_prune'] = [ now, []]
            
      self._cache[key] = [ cache_time, data ]
      return data
        
        
    def _ad_search(self, base_dn=None, scope=ldap.SCOPE_BASE, filter=None, attrs=[]):
      #self.env.log.debug('searching for: %s' % filter)
      #-- get current time for cache
      current_time = time.time()
      
      #-- create unique key from the filter and the
      keystr = ",".join([ base_dn, str(scope), filter, ":".join(attrs) ])
      key = md5.new(keystr).hexdigest()
      # self.log.debug('searching for %s(%s)' % (filter, key))
      
      #-- check memcache
      #   we do this to reduce network usage.
      ret = self._cache_get(key)
      if ret:
         return ret
      
      #--  Check database
      db=self.env.get_db_cnx()
      cur = db.cursor()
      cur.execute('SELECT lut,data FROM ad_cache WHERE id="%s"' % key)
      row = cur.fetchone()
      if row:      
         lut,data = row
         
         if current_time < lut+int(self.cache_ttl):
            self.env.log.debug('dbcache hit for %s' % filter)
            ret = cPickle.loads(str(data))
            self._cache_set(key,ret,lut)
            return ret
         else: 
           #-- old data, delete it and anything else that's old.
           cur.execute('DELETE FROM ad_cache WHERE lut < %s' % (current_time-int(self.cache_ttl)) )
           db.commit()
      
      #-- check AD
      ad = self._bind_ad()
      adr = ad.search_s(base_dn.encode(self.charset), scope, filter, attrs)
      
      if adr:
        self.log.debug('AD hit for %s', filter)
        
      #-- set the data in the cache for the next search, even empty results
      adr_str=cPickle.dumps(adr,0)
      try:
          cur=db.cursor()
          cur.execute('INSERT INTO ad_cache (id, lut, data) VALUES (%s, %s, %s)', [str(key), int(current_time), buffer(adr_str)])
          db.commit()
           
      except Exception, e:
        db.rollback()
        self.log.warn('db cache update failed. %s' % e )
      
      #-- set the data in the memcache 
      self._cache_set(key, adr)
            
      return adr
        
