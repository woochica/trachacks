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
import time, types, hashlib
import cPickle

from acct_mgr.api import IPasswordStore
from trac.perm import IPermissionGroupProvider
from tracext.adauth.api import IPermissionUserProvider

GROUP_PREFIX = '@'
NOCACHE = 0

__all__ = ['ADAuthStore']

class ADAuthStore(Component):
    """AD Password Store for Account Manager """

    implements(IPasswordStore, IPermissionUserProvider, IPermissionGroupProvider)

    dir_uri = Option('account-manager', 'dir_uri', 'ldap://localhost', 'URI of the LDAP or Active Directory Server')
    dir_charset = Option('account-manager', 'dir_charset', 'utf-8', 'Text encoding used by the LDAP or Active Directory Server') 
    dir_scope = Option('account-manager', 'dir_scope', 1, '0=Base, 1=OneLevel, 2=Subtree')
    dir_binddn = Option('account-manager', 'dir_binddn', '', 'DN used to bind to AD, leave blank for anonymous bind')
    dir_bindpw = Option('account-manager', 'dir_bindpw', '', 'Password used when binding to AD, leave blank for anonymous bind')
    dir_timeout = Option('account-manager', 'dir_timeout', 5, 'ldap response timeout in seconds')
    dir_basedn = Option('account-manager', 'dir_basedn', None, 'Base DN used for account searches')
    user_attr = Option('account-manager', 'user_attr', 'sAMAccountName', 'attribute of the user in the directory')
    name_attr = Option('account-manager', 'name_attr', 'displayName', 'attribute of the users name in the directory')
    email_attr = Option('account-manager', 'email_attr', 'mail', 'attribute of the users email in the directory')
    group_basedn = Option('account-manager', 'group_basedn', None, 'Base DN used for group searches')
    group_attr = Option('account-manager', 'group_attr', 'cn', 'Attribute of the name of the group')
    group_validusers = Option('account-manager', 'group_validusers', None, 'DN of group containing valid users. If None, any AD user is valid')
    group_tracadmin = Option('account-manager', 'group_tracadmin', None, 'DN of group containing TRAC_ADMIN users (can also assign TRAC_ADMIN to an LDAP group.)')
    group_expand = Option('account-manager', 'group_expand', 1, 'binary: expand ldap_groups into trac groups.')
    group_member_attr = Option('account-manager', 'group_member_attr', 'member', 'which group attribute to check for members')
    group_member_value = Option('account-manager', 'group_member_value', 'dn', 'what to look for in the member_attr')
    cache_ttl = Option('account-manager', 'cache_timeout', 60, 'cache timeout in seconds')
    cache_memsize = Option('account-manager', 'cache_memsize', 400, 'size of memcache in entries, zero to disable')
    cache_memprune = Option('account-manager', 'cache_memprune', 5, 'percent of entries to prune')
    cache_memsize_warn = Option('account-manager', 'cache_memsize_warn', 300, 'warning message for cache pruning in seconds')
    
    def __init__(self, ldap=None):
        #-- cache my ldap handle
        self._ldap = ldap
        #-- have a memory cache
        self._cache = {}
        
    # IPasswordStore
    def config_key(self):
        """Deprecated"""

    #-- this is changed to use logged in users from the session table,
    #   because an ldap search would be untenable.
    def get_users(self, populate_session=True):
      """Grab a list of users from the session store"""
      #-- check memcache
      userlist = self._cache_get('allusers')
      if userlist:
        return userlist
      
      #-- cache miss.. goto session table
      userlist = []
      userinfo = self.env.get_known_users()
      for user in userinfo:
          userlist.append(user[0])
        
      if userlist: 
          self.log.debug('userlist: %s ' % ",".join(userlist))
      
      self._cache_set('allusers', userlist)
      return userlist

    #-- this will be expensive on large groups.  
    def expand_group_users(self, group_dn):
      """Given a group name, enumerate all members"""
      #-- check memcache
      users = self._cache_get(group_dn)
      if users:
         return users
       
      #-- where to look
      basedn = self.group_basedn or self.dir_basedn
              
      users = []
      if self.group_expand:
        group_member_attr = self.group_member_attr.decode('ascii')
        groupfilter = '(%s)' % (group_dn.split(',')[0])
        g = self._dir_search(basedn, self.dir_scope, groupfilter, [group_member_attr])
        if g and g[0][1].has_key(group_member_attr):
            users = []
            for m in g[0][1][group_member_attr]:
              m_filter = '(%s)' % (m.split(',')[0])
              e = self._dir_search(basedn, self.dir_scope, m_filter)
              if e:
                 if 'person' in e[0][1]['objectClass']:
                   users.append(self._get_userinfo(e[0][1]))
                 elif 'group' in e[0][1]['objectClass']:
                   users.extend(self.expand_group_users(e[0][0].decode(self.dir_charset)))
                 else:
                   self.log.debug('The group member (%s) is neither a group nor a person' % e[0][0])
              else:
                self.log.debug('Unable to find user %s listed in group: %s' % str(m))
                self.log.debug('This is very strange and you should probably check '
                                 'the consistency of your LDAP directory.' % str(m))
          
        #-- dedupe and sort list
        users = sorted(list(set(users)))
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
    
    #-- we do several things with this step to clear the caches and update session attributes
    def check_password(self, user, password):
        """Checks the password against LDAP"""
        
        success = None
        msg = "User Login: %s" % str(user)
        
        dn = self._get_user_dn(user, NOCACHE)
        if dn:
            success = self._bind_dir(dn, password) or False
            if success:
              msg += " Password Verified"
              success = True
            elif success is False:
              msg += " Password Failed"
            self.log.info(msg)
        else:
            msg += " does not exist, deferring authentication"
            self.log.info(msg)
            return success
          
        #-- check the group_validusers if used
        if self.group_validusers:
          valid_users = [u[0] for u in self.expand_group_users(self.group_validusers)]
          if not user in valid_users:
            msg += " but user is not in %s" % self.group_validusers
            self.log.info(msg)
            return False
             
        #-- update the session data at each login, 
        #   note the use of NoCache to force the update(s)
        attrs = [ self.user_attr, 'mail', 'proxyAddress', 'displayName']
        filter = "(&(%s=%s)(objectClass=person))" % (self.user_attr, user)
        users = self._dir_search(self.dir_basedn, self.dir_scope, filter, attrs, NOCACHE)
        
        if not users:
            raise TracError('Weird! authenticated, but didnt find the user with filter : %s (%s)' % (filter, users))
        
        #-- this is where we update the session table to make this a valid user.
        userinfo = self._get_userinfo(users[0][1])
        self._populate_user_session(userinfo)
        
        #-- update the users and groups by doing a search w/o cache
        groups = self.get_permission_groups(user, NOCACHE)
        users = self.get_users(NOCACHE)
        
        return success

    def delete_user(self, user):
        """Can't delete from LDAP"""
        self.log.debug("Can not delete users from Active Directory")
        return False

    # IPermissionUserProvider
    def get_permission_action(self, username):
        """ Return TRAC_ADMIN if user is in the self.group_tracadmin """

        if self.group_tracadmin:
            users = [u[0] for u in self.expand_group_users(self.group_tracadmin)]
            if username in users:
                self.log.debug("User is in %", self.group_tracadmin)
                return ['TRAC_ADMIN']
        return []
      
    # IPermissionGroupProvider
    def get_permission_groups(self, username, use_cache=1):
        """Return a list of names of the groups that the user with the 
        specified name is a member of."""
        
        if use_cache:
            groups = self._cache_get('groups:%s' % username)
            if groups:
              return groups
        
        # get dn
        dn = self._get_user_dn(username)
        if not self.group_member_attr or self.group_member_attr == 'dn': 
       
           filter = "(&(%s=%s)(objectClass=person))" % (self.user_attr, user)
           users = self._dir_search(self.dir_basedn, self.dir_scope, filter, [self.group_member_dn.encode('ascii')], NOCACHE)
           group_value = users[0][1][self.user_attr.encode('ascii')]
        else: 
           group_value = dn
        
        if group_value: 
            # retrieves the user groups from LDAP
            groups = self._get_user_groups(self.group_member_attr, group_value)
            if groups:
                self.env.log.debug('%s has LDAP groups: %s' % (username, ','.join(groups)))
            else:
                self.env.log.debug('username %s (%s) has no LDAP groups', username, dn)
                
            self._cache_set('groups:%s' % username, groups)
            return groups
                
        else:
            self.log.debug("username: %s has no dn." % username)
            return []
      
    # Internal methods
    def _bind_dir(self, user_dn=None, passwd=None):
      
        #-- what do we connect to
        if not self.dir_uri:
            raise TracError('The dir_uri ini option must be set')
          
        if not self.dir_uri.lower().startswith('ldap'):
            raise TracError('The dir_uri URI must be start with ldaps?://')
          
        #-- if user auth .. only return success
        if user_dn and passwd: 
            # setup the ldap connection.. init does NOT attempt a connection, but search does.
            # ldap.ReconnectLDAPObject(uri [, trace_level=0 [, trace_file=sys.stdout [, trace_stack_limit=5] [, retry_max=1 [, retry_delay=60.0]]]])
            user_ldap = ldap.ldapobject.ReconnectLDAPObject(self.dir_uri, 0, '', 0, 2, 1)
        
            self.log.debug('_bind_dir: attempting specific bind to %s as %s' % (self.dir_uri, user_dn))
            try:
                user_ldap.simple_bind_s(user_dn, passwd)
            except Exception, e:
                self.log.error('_bind_dir: binding failed. %s ' % (e))
                return None
            return 1
            
        #-- return cached handle for default use
        if self._ldap:
            return self._ldap
            
        # setup the ldap connection.. init does NOT attempt a connection, but search does.
        self._ldap = ldap.ldapobject.ReconnectLDAPObject(self.dir_uri, retry_max=5, retry_delay=1)
        
        if self.dir_binddn:
          self.log.debug('_bind_dir: attempting general bind to %s as %s' % (self.dir_uri, self.dir_binddn))
        else: 
          self.log.debug('_bind_dir: attempting general bind to %s anonymously' % self.dir_uri)
          
        try:
            self._ldap.simple_bind_s(self.dir_binddn, self.dir_bindpw)
        except ldap.LDAPError, e:
            self.log.info('bind_ad: binding failed. %s ' % (e))
            raise TracError('cannot bind to %s: %s' % (self.dir_uri , en))
        
        self.log.info('Bound to %s correctly.' % self.dir_uri)
          
        #-- allow restarting
        self._ldap.set_option(ldap.OPT_RESTART, 1)
        self._ldap.set_option(ldap.OPT_TIMEOUT, int(self.dir_timeout))
        
        return self._ldap
   
   ### searches
    def _get_user_dn(self, user, cache=1):
        """ Get users dn """
          
        dn = self._cache_get('dn: %s' % user)
        if dn:
          return dn
            
        u = self._dir_search(self.dir_basedn, self.dir_scope,
                                "(&(%s=%s)(objectClass=person))" % (self.user_attr, user),
                                [self.user_attr], cache)

        if not u:
           self.log.debug('user not found: %s' % user)
           dn = None
        else:
           dn = u[0][0]
           self._cache_set('dn: %s' % user, dn)
           self.log.debug('user %s has dn: %s' % (user, dn))
        return dn
      
    def _get_user_groups(self, attr, value):
        """Returns a list of all groups a user belongs to"""
        
        basedn = self.group_basedn or self.dir_basedn
        groups = self._cache_get('groups: %s' % value)
        if groups:
          return groups
        
        groups = []
        group_name_attr = self.group_attr.encode('ascii') or self.user_attr.encode('ascii')
        dir_groups = self._dir_search(basedn, self.dir_scope,
                                     '(&(%s=%s)(objectClass=group))' % (attr, value),
                                     [group_name_attr])
        
        # TODO - write this to handle memberOf as well
        # append 
        if dir_groups: 
          for group in dir_groups:
            tgroup = GROUP_PREFIX + group[1][group_name_attr][0].lower().replace(' ', '_')
            if tgroup not in groups:
              groups.append(tgroup)
                               
        groups.sort()
        
        self.log.debug('user:%s groups: %s' % (value, ",".join(groups)))
        self._cache_set('groups: %s' % value, groups)
        return groups
              

    def _get_userinfo(self, attrs):
        """ Extract the userinfo tuple from the LDAP search result """
        
        username = attrs[self.user_attr][0].lower()
        displayname = attrs.get(self.name_attr, [''])[0]
        email = ''
        if self.email_attr in attrs:
            email = attrs[self.email_attr][0].lower()
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
        (uname, displayname, email) = userinfo
        
        db = self.env.get_db_cnx()
        cur = db.cursor()
        try:
            cur.execute('INSERT INTO session (sid, authenticated, last_visit) VALUES (%s, 1, %s)' % (uname, 0))
        except:
            self.log.debug('session for %s exists.' % uname)
            
        #-- assume enabled if we get this far
        #   self.env.get_known_users() needs this.. 
        # TODO need to have it updated by the get_dn stuff long term so the db matches the auth source.
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO session_attribute (sid, authenticated, name, value) VALUES ('%s', 1, 'enabled', '1')" % (uname))
        except:
            self.log.debug('session for %s exists.' % uname)
        
            
        #-- we want to update these regardless.
        if email:
            cur = db.cursor()
            cur.execute("INSERT OR REPLACE INTO session_attribute (sid, authenticated, name, value) "
                            "VALUES ('%s', 1, 'email', '%s')" % (uname, to_unicode(email)))
            self.log.info('updating user session email info for %s (%s)' % (uname, to_unicode(email)))
            
        if displayname:
            cur = db.cursor()
            cur.execute("INSERT OR REPLACE INTO session_attribute "
                            "(sid, authenticated, name, value) VALUES ('%s', 1, 'name', '%s')" % (uname, to_unicode(displayname)))
            self.log.info('updating user session displayname info for %s (%s)' % (uname, to_unicode(displayname)))
        db.commit()
        return db.close()
        
    def _cache_get(self, key=None, ttl=None):
        """Get an item from memory cache"""
        cache_ttl = ttl or self.cache_ttl
        if not self.cache_memsize:
          return None;
        
        now = time.time()
            
        if key in self._cache:
            lut, data = self._cache[key]            
            if lut + int(cache_ttl) >= now:
              self.env.log.debug('memcache hit for %s' % key)
              return data
            else: 
             del self._cache[key] 
        return None
    
    def _cache_set(self, key=None, data=None, cache_time=None):
      if not self.cache_memsize:
        return None
      #-- figure out time
      now = time.time()
      if not cache_time:
        cache_time = now
         
      #-- prune if we need to 
      if len(self._cache) > int(self.cache_memsize):
        #-- warn if too frequent
        if 'last_prune' in self._cache:
          last_prune, data = self._cache['last_prune']
          if last_prune + self.cache_memsize_warn > now:
            self.env.log.info('pruning memcache in less than %d seconds, you might increase cache_memsize.' % int(self.cache_memsize_warn))
                
        self.env.log.debug('pruning memcache by %d: (current: %d > max: %d )' % (self.cache_memprune, len(self._cache), int(self.cache_memsize)))
        cache_keys = self._cache.keys()
        cache_keys.sort(lambda x, y: cmp(self._cache[x][0],
                                           self._cache[y][0]))
        # discards the 10% oldest
        old_keys = cache_keys[:(int(self.cache_memprune) * int(self.cache_memsize)) / 100]
        for k in old_keys:
           del self._cache[k]
        self._cache['last_prune'] = [ now, []]
            
      self._cache[key] = [ cache_time, data ]
      return data
    
    def _decode_list(self, list=None):
      newlist = []
      if not list:
        return list
      for val in list:
          newlist.append(val.encode('ascii', 'ignore'))
      return newlist        
    
    def _dir_search(self, basedn=None, scope=1, filter=None, attrs=[], check_cache=1):
      #self.env.log.debug('searching for: %s' % filter)
      #-- get current time for cache
      current_time = time.time()
      
      attrs = self._decode_list(attrs)
      
      #-- sanity
      if not basedn:
        raise TracError('basedn not defined!')
      if not filter:
        raise TracError('filter not defined!')
      
      #-- create unique key from the filter and the
      keystr = ",".join([ basedn, str(scope), filter, ":".join(attrs) ])
      key = hashlib.md5(keystr).hexdigest()
      self.log.debug('_dir_search: searching %s for %s(%s)' % (basedn, filter, key))
      
      db = self.env.get_db_cnx()
      
      #-- check memcache
      #   we do this to reduce network usage.
      if check_cache: 
          ret = self._cache_get(key)
          if ret:
             return ret
      
          #--  Check database
          cur = db.cursor()
          cur.execute("""SELECT lut,data FROM ad_cache WHERE id=%s""", [key])
          row = cur.fetchone()
          if row:      
             lut, data = row
         
             if current_time < lut + int(self.cache_ttl):
                self.env.log.debug('dbcache hit for %s' % filter)
                ret = cPickle.loads(str(data))
                self._cache_set(key, ret, lut)
                return ret
             else: 
               #-- old data, delete it and anything else that's old.
               lut = str(current_time - int(self.cache_ttl)) 
               cur.execute("""DELETE FROM ad_cache WHERE lut < %s""", [lut])
               db.commit()
      else:
        self.log.debug('_dir_search: skipping cache.')
      
      #-- check Directory
      dir = self._bind_dir()
      self.log.debug('_dir_search: starting LDAP search of %s %s using %s for %s ' % (self.dir_uri, basedn, filter, attrs))
      
      try:
        res = dir.search_s(basedn.encode(self.dir_charset), scope, filter, attrs)
      except ldap.LDAPError, e:
        self.log.error('Error searching : %s', e)
        
      #-- did we get a result?
      if res:
        self.log.debug('_dir_search: AD hit, %d entries.', len(res))
      else:
        self.log.debug('_dir_search: AD miss.')
        
      #-- return if not caching
      if not check_cache:
        return res
        
      #-- set the data in the db cache for the next search, even empty results
      res_str = cPickle.dumps(res, 0)
      try:
          cur = db.cursor()
          cur.execute("""INSERT OR REPLACE INTO ad_cache (id, lut, data) 
                         VALUES (%s, %i, %s)""", ( str(key), int(current_time), buffer(res_str)))
          db.commit()
           
      except Exception, e:
        db.rollback()
        self.log.warn('_dir_search: db cache update failed. %s' % e)
      
      #-- set the data in the memcache 
      self._cache_set(key, res)
            
      return res
