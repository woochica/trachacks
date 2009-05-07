# -*- coding: utf-8 -*-
#
# LDAP permission extensions for Trac
# 
# Copyright (C) 2003-2006 Edgewall Software
# Copyright (C) 2005-2006 Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Warning: this plug in has not been extensively tested, and may have security
# issues. Do not use this plugin on production servers where security is 
# a concern.
# Requires Python-LDAP, available from http://python-ldap.sourceforge.net
#

import re
import time
import ldap

from trac.core import *
from trac.perm import IPermissionGroupProvider, IPermissionStore
from trac.config import _TRUE_VALUES

LDAP_MODULE_CONFIG = [ 'enable', 'permfilter', 
                       'global_perms', 'manage_groups'
                       'cache_ttl', 'cache_size',
                       'group_bind', 'store_bind',
                       'user_rdn', 'group_rdn' ]

LDAP_DIRECTORY_PARAMS = [ 'host', 'port', 'use_tls', 'basedn',
                          'bind_user', 'bind_passwd',
                          'groupname', 'groupmember', 'groupmemberisdn',
                          'groupattr', 'uidattr', 'permattr']
                          
GROUP_PREFIX = '@'

# regular expression to explode a DN into a (attr, rdn, basedn)
DN_RE = re.compile(r'^(?P<attr>.+?)=(?P<rdn>.+?),(?P<base>.+)$')

class LdapPermissionGroupProvider(Component):
    """
    Provides permission groups from a LDAP directory
    """
    implements(IPermissionGroupProvider)

    def __init__(self, ldap=None):
        # looks for groups only if LDAP support is enabled
        self.enabled = self.config.getbool('ldap', 'enable')
        if not self.enabled:
            return
        self.util = LdapUtil(self.config)
        # LDAP connection
        self._ldap = ldap
        # LDAP connection config
        self._ldapcfg = {}
        for name,value in self.config.options('ldap'):
            if name in LDAP_DIRECTORY_PARAMS:
                self._ldapcfg[name] = value
        # user entry local cache
        self._cache = {}
        # max time to live for a cache entry
        self._cache_ttl = int(self.config.get('ldap', 'cache_ttl', str(15*60)))
        # max cache entries
        self._cache_size = min(25, int(self.config.get('ldap', 'cache_size', 
                                                       '100')))

    # IPermissionProvider interface

    def get_permission_groups(self, username):
        """Return a list of names of the groups that the user with the 
        specified name is a member of."""

        # anonymous and authenticated groups are set with the default provider
        groups = []
        if not self.enabled:
            return groups
                        
        # stores the current time for the request (used for the cache)
        current_time = time.time()
        
        # test for if username in the cache
        if username in self._cache:
            # cache hit
            lut, groups = self._cache[username]
        
            # ensures that the cache is not too old
            if current_time < lut+self._cache_ttl:
                # sources the cache
                # cache lut is not updated to ensure
                # it is refreshed on a regular basis
                self.env.log.debug('cached (%s): %s' % \
                                   (username, ','.join(groups)))
                return groups
        
        # cache miss (either not found or too old)
        if not self._ldap:
            # new LDAP connection
            bind = self.config.getbool('ldap', 'group_bind')
            self._ldap = LdapConnection(self.env.log, bind, **self._ldapcfg)
        
        # retrieves the user groups from LDAP
        ldapgroups = self._get_user_groups(username)
        # if some group is found
        if ldapgroups:
            # tests for cache size
            if len(self._cache) >= self._cache_size:
                # the cache is becoming too large, discards
                # the less recently uses entries
                cache_keys = self._cache.keys()
                cache_keys.sort(lambda x,y: cmp(self._cache[x][0], 
                                                self._cache[y][0]))
                # discards the 5% oldest
                old_keys = cache_keys[:(5*self._cache_size)/100]
                for k in old_keys:
                    del self._cache[k]
        else:
            # deletes the cache if there's no group for this user
            # for debug, until a failed LDAP connection returns an error...
            if username in self._cache:
                del self._cache[username]
        
        # updates the cache
        self._cache[username] = [current_time, ldapgroups]
        
        # returns the user groups
        groups.extend(ldapgroups)
        if groups:
            self.env.log.debug('groups: ' + ','.join(groups))

        return groups

    def flush_cache(self, username=None):
        """Invalidate the entire cache or a named entry"""
        if username is None:
            self._cache = {}
        elif self._cache.has_key(username):
            del self._cache[username]
        
    # Private API
    
    def _get_user_groups(self, username):
        """Returns a list of all groups a user belongs to"""
        ldap_groups = self._ldap.get_groups()
        groups = []
        for group in ldap_groups:
            if self._ldap.is_in_group(self.util.user_attrdn(username), group):
                m = DN_RE.search(group)
                if m:
                    groupname = GROUP_PREFIX + m.group('rdn')
                    if groupname not in groups:
                        groups.append(groupname)
        return groups

class LdapPermissionStore(Component):
    """
    Stores and manages permissions with a LDAP directory backend
    """
    implements(IPermissionStore)

    group_providers = ExtensionPoint(IPermissionGroupProvider)

    def __init__(self, ldap=None):
        # looks for groups only if LDAP support is enabled
        self.enabled = self.config.getbool('ldap', 'enable')
        if not self.enabled:
            return
        self.util = LdapUtil(self.config)
        # LDAP connection
        self._ldap = ldap
        # LDAP connection config
        self._ldapcfg = {}
        for name,value in self.config.options('ldap'):
            if name in LDAP_DIRECTORY_PARAMS:
                self._ldapcfg[name] = value
        # user entry local cache
        self._cache = {}
        # max time to live for a cache entry
        self._cache_ttl = int(self.config.get('ldap', 'cache_ttl', str(15*60)))
        # max cache entries
        cache_size = self.config.get('ldap', 'cache_size', '100')
        self._cache_size = min(25, int(cache_size))
        # environment name
        envpath = self.env.path.replace('\\','/')
        self.env_name = envpath[1+envpath.rfind('/'):]
        # use directory-wide permissions
        self.global_perms = self.config.getbool('ldap', 'global_perms')
        self.manage_groups = self.config.getbool('ldap', 'manage_groups')

    # IPermissionStore interface

    def get_user_permissions(self, username):
        """Retrieves the user permissions from the LDAP directory"""
        if not self.enabled:
            raise TracError("LdapPermissionStore is not enabled")
        actions = self._get_cache_actions(username)
        if not actions:
            users = [username]
            for provider in self.group_providers:
                users += list(provider.get_permission_groups(username))
            for user in users:
                uid = self.util.create_dn(user)
                for action in self._get_permissions(uid):
                    if action not in actions:
                        actions.append(action)

            self.env.log.debug('new: %s' % actions)
            self._update_cache_actions(username, actions)
        perms = {}
        for action in actions: 
                perms[action] = True
        return perms

    def get_users_with_permissions(self, permissions):
        """Retrieve a list of users that have any of the specified permissions.
        """
        users = set([u[0] for u in self.env.get_known_users()])
        result = set()
        for user in users:
            userperms = self.get_user_permissions(user)
            for group in permissions:
                if group in userperms:
                    result.add(user)
        return list(result)

    def get_all_permissions(self):
        """Retrieve the permissions for all users from the LDAP directory"""
        # do not use the cache as this method is only used for administration
        # tasks, not for runtime
        if not self.enabled:
            raise TracError("LdapPermissionStore is not enabled")
        perms = []
        filterstr = self.config.get('ldap', 'permfilter', 'objectclass=*')
        basedn = self.config.get('ldap','basedn','').encode('ascii')
        self._openldap()
        dns = self._ldap.get_dn(basedn, filterstr.encode('ascii'))
        permusers = []
        for dn in dns:
            user = self.util.extract_user_from_dn(dn)
            if not user or user in permusers: continue
            permusers.append(user)
            self.log.debug("permission for %s (%s)" % (user, dn))
            actions = self._ldap.get_attribute(dn, self._ldap.permattr)
            for action in actions:
                xaction = self._extract_action(action)
                if not xaction:
                    continue
                perms.append((user, xaction))
            if self.manage_groups:
                for provider in self.group_providers:
                    if isinstance(provider, LdapPermissionGroupProvider):
                        for group in provider.get_permission_groups(user):
                            perms.append((user, group))
        return perms

    def grant_permission(self, username, action):
        """Store the new permission for the user in the LDAP directory"""
        if not self.enabled:
            raise TracError("LdapPermissionStore is not enabled")
        if self.manage_groups and self.util.is_group(action):
            self._flush_group_cache(username)
            self._add_user_to_group(username.encode('ascii'), action)
            return
        uid = self.util.create_dn(username.encode('ascii'))
        try:
            permlist = self._get_permissions(uid)
            action = action.encode('ascii')
            if action not in permlist:
                xaction = self._build_action(action)
                self._ldap.add_attribute(uid, self._ldap.permattr, xaction)
            if self.util.is_group(username):
                # flush the cache as group dependencies are not known 
                self.flush_cache()
            else:
                self.flush_cache(username)
                self._add_cache_actions(username, [action])
        except ldap.LDAPError, e:
            raise TracError, "Unable to grant permission %s to %s: %s" \
                             % (action, username, e[0]['desc'])

    def revoke_permission(self, username, action):
        """Remove the permission for the user from the LDAP directory"""
        if not self.enabled:
            raise TracError("LdapPermissionStore is not enabled")
        if self.manage_groups and self.util.is_group(action):
            self._flush_group_cache(username)
            self._remove_user_from_group(username.encode('ascii'), action)
            return
        uid = self.util.create_dn(username.encode('ascii'))
        try:
            permlist = self._get_permissions(uid)
            if action in permlist:
                action = action.encode('ascii')
                xaction = self._build_action(action)
                self._ldap.delete_attribute(uid, self._ldap.permattr, xaction)
                if self.util.is_group(username):
                    # flush the cache as group dependencies are not known 
                    self.flush_cache()
                else:
                    self.flush_cache(username)
                    self._del_cache_actions(username, [action])
        except ldap.LDAPError, e:
            kind = self.global_perms and 'global' or 'project'
            raise TracError, "Unable to revoke %s permission %s from %s: %s" \
                             % (kind, action, username, e[0]['desc'])

    # Private implementation

    def _openldap(self):
        """Open a new connection to the LDAP directory"""
        if self._ldap is None: 
            bind = self.config.getbool('ldap', 'store_bind')
            self._ldap = LdapConnection(self.env.log, bind, **self._ldapcfg)

    def _get_permissions(self, uid):
        """Retrieves the permissions from the LDAP directory"""
        self._openldap()
        actions = self._ldap.get_attribute(uid, self._ldap.permattr) 
        perms = []
        for action in actions:
            if action not in perms:
                xaction = self._extract_action(action)
                if xaction:
                    perms.append(xaction)
        return perms

    def _extract_action(self, action):
        """Filters the actions (global or per-project action)"""
        items = action.split(':')
        if len(items) == 1:
            # no environment, consider global
            return action
        (name, xaction) = items
        if name == self.env_name:
            # environment, check it
            return xaction
        return None

    def _build_action(self, action):
        """Creates a global or per-project LDAP action"""
        if self.global_perms:
            return action
        return "%s:%s" % (self.env_name, action)

    def _add_user_to_group(self, user, group):
        groupdn = self.util.create_dn(group)
        userdn = self.util.create_dn(user)
        self._openldap()
        try:
            self._ldap.add_attribute(groupdn, self._ldap.groupmember, userdn)
            self.log.info("user %s added to group %s" % (user, group))
        except ldap.TYPE_OR_VALUE_EXISTS, e:
            # already in group, can safely ignore
            self.log.debug("user %s already member of %s" % (user, group))
            return
        except ldap.LDAPError, e:
            raise TracError, e[0]['desc']
        
    def _remove_user_from_group(self, user, group):
        groupdn = self.util.create_dn(group)
        userdn = self.util.create_dn(user)
        self._openldap()
        try:
            self._ldap.delete_attribute(groupdn, self._ldap.groupmember, 
                                        userdn)
            self.log.info("user %s removed from group %s" % (user, group))
        except ldap.OBJECT_CLASS_VIOLATION, e:
            # probable cause is an empty group
            raise TracError, "Ldap error (group %s would be emptied?)" % group
        except ldap.LDAPError, e:
            raise TracError, e[0]['desc']
        
    def _get_cache_actions(self, username):
        """Retrieves the user permissions from the cache, if any"""
        if username in self._cache:
            lut, actions = self._cache[username]
            if time.time() < lut+self._cache_ttl:
                self.env.log.debug('cached (%s): %s' % \
                                   (username, ','.join(actions)))
                return actions
        return []
    
    def _add_cache_actions(self, username, newactions):
        """Add new user actions into the cache"""
        self._cleanup_cache()
        if username in self._cache:
            lut, actions = self._cache[username]
            for action in newactions:
                if action not in actions:
                    actions.append(action)
            self._cache[username] = [time.time(), actions]
        else:
            self._cache[username] = [time.time(), newactions]            
    
    def _del_cache_actions(self, username, delactions):
        """Remove user actions from the cache"""
        if not username in self._cache:
            return
        lut, actions = self._cache[username]
        newactions = []
        for action in actions:
            if action not in delactions:
                newactions.append(action)
        if len(newactions) == 0:
            del self._cache[username]
        else:
            self._cache[username] = [time.time(), newactions]
    
    def _update_cache_actions(self, username, actions):
        """Set the cache entry for the user with the new actions"""
        # if not action, delete the cache entry
        if len(actions) == 0:
            if username in self._cache:
                del self._cache[username]
            return
        self._cleanup_cache()
        # overwrite the cache entry with the new actions
        self._cache[username] = [time.time(), actions]
    
    def _cleanup_cache(self):
        """Make sure the cache is not full or discard oldest entries"""
        # if cache is full, removes the LRU entries
        if len(self._cache) >= self._cache_size:
            cache_keys = self._cache.keys()
            cache_keys.sort(lambda x,y: cmp(self._cache[x][0], 
                                            self._cache[y][0]))
            old_keys = cache_keys[:(5*self._cache_size)/100]
            self.log.info("flushing %d cache entries" % len(old_keys))
            for k in old_keys:
                del self._cache[k]
                
    def flush_cache(self, username=None):
        """Delete all entries in the cache"""
        if username is None:
            self._cache = {}
        elif self._cache.has_key(username):
            del self._cache[username]
        # we also need to flush the LDAP permission group provider
        self._flush_group_cache(username)
            
    def _flush_group_cache(self, username=None):
        """Flush the group cache (if in use)"""
        if self.manage_groups:
            for provider in self.group_providers:
                if isinstance(provider, LdapPermissionGroupProvider):
                    provider.flush_cache(username)

class LdapUtil(object):
    """Utilities for LDAP data management"""
        
    def __init__(self, config):
        for k, default in [('groupattr', 'cn'), 
                           ('uidattr', 'uid'),
                           ('basedn', None),
                           ('user_rdn', None),
                           ('group_rdn', None)]:
            v = config.get('ldap', k, default)
            if v: v = v.encode('ascii').lower()
            self.__setattr__(k, v)
            
    def is_group(self, username):
        return username.startswith(GROUP_PREFIX)
            
    def create_dn(self, username):
        """Create a user or group LDAP DN from his/its name"""
        if username.startswith(GROUP_PREFIX):
            return self.group_attrdn(username[len(GROUP_PREFIX):])
        else:
            return self.user_attrdn(username)

    def group_attrdn(self, group):
        """Build the dn for a group"""
        if self.group_rdn:
            return "%s=%s,%s,%s" % \
                   (self.groupattr, group, self.group_rdn, self.basedn)
        else:
            return "%s=%s,%s" % (self.groupattr, group, self.basedn)
            
    def user_attrdn(self, user):
        """Build the dn for a user"""
        if self.user_rdn:
            return "%s=%s,%s,%s" % \
                   (self.uidattr, user, self.user_rdn, self.basedn)
        else:
            return "%s=%s,%s" % (self.uidattr, user, self.basedn)
            
    def extract_user_from_dn(self, dn):
        m = DN_RE.search(dn)
        if m:
            sub = m.group('base').lower()
            basednlen = len(self.basedn)
            if sub[len(sub)-basednlen:].lower() != self.basedn:
                return None
            rdn = sub[:-basednlen-1]
            if rdn == self.group_rdn:
                if m.group('attr').lower() == self.groupattr:
                    return GROUP_PREFIX + m.group('rdn')
            elif rdn == self.user_rdn:
                if m.group('attr').lower() == self.uidattr:
                    return m.group('rdn')
        return None
                
class LdapConnection(object):
    """
    Wrapper class for the LDAP directory
    Use only synchronous LDAP calls
    """
    
    _BOOL_VAL = ['groupmemberisdn', 'use_tls']
    _INT_VAL  = ['port']  
        
    def __init__(self, log, bind=False, **ldap):
        self.log = log
        self.bind = bind
        self.host = 'localhost'
        self.port = None
        self.groupname = 'groupofnames'
        self.groupmember = 'member'
        self.groupattr = 'cn'
        self.uidattr = 'uid'
        self.permattr = 'tracperm'
        self.bind_user = None
        self.bind_passwd = None
        self.basedn = None
        self.groupmemberisdn = True
        self.use_tls = False
        for k, v in ldap.items():
            if k in LdapConnection._BOOL_VAL:
                self.__setattr__(k, v.lower() in _TRUE_VALUES)
            elif k in LdapConnection._INT_VAL:
                self.__setattr__(k, int(v))
            else:
                if isinstance(v, unicode):
                    v = v.encode('ascii')
                self.__setattr__(k, v)
        if self.basedn is None:
            raise TracError, "No basedn is defined"
        if self.port is None:
            self.port = self.use_tls and 636 or 389
            
    def close(self):
        """Close the connection with the LDAP directory"""
        self._ds.unbind_s()
        self._ds = None

    def get_groups(self):
        """Return a list of available group dns"""
        groups = self.get_dn(self.basedn, 'objectclass=' + self.groupname)
        return groups
    
    def is_in_group(self, userdn, groupdn):
        """Tell whether the uid is member of the group"""
        if self.groupmemberisdn:
            udn = userdn 
        else:
            m = re.match('[^=]+=([^,]+)', userdn)
            if m is None:
                self.log.warn('Malformed userdn: %s' % userdn)
                return False
            udn = m.group(1) 
        for attempt in range(2):
            cr = self._compare(groupdn, self.groupmember, udn)
            if self._ds:
                return cr
        return False

    def get_dn(self, basedn, filterstr):
        """Return a list of dns that satisfy the LDAP filter"""
        dns = []
        for attempt in range(2):
            sr = self._search(basedn, filterstr, ['dn'], ldap.SCOPE_SUBTREE)
            if sr:
                for (dn, attrs) in sr:
                    dns.append(dn)
                break
            if self._ds:
                break
        return dns

    def get_attribute(self, dn, attr):
        """Return the values of the attribute of the dn entry"""
        attributes = [ attr ]
        (filt, base) = dn.split(',', 1)
        values = []
        for attempt in range(2):
            sr = self._search(base, filterstr=filt, attributes=attributes)
            if sr:
                for (dn, attrs) in sr:
                    if attrs.has_key(attr):
                        values = attrs[attr]
                break
            if self._ds:
                break
        return values

    def add_attribute(self, dn, attr, value):
        """Add a new value to the attribute of the dn entry"""
        try:
            if not self.__dict__.has_key('_ds') or not self.__dict__['_ds']:
                self._open()
            self._ds.modify_s(dn, [(ldap.MOD_ADD, attr, value)]) 
        except ldap.LDAPError, e:
            self.log.error("unable to add attribute '%s' to uid '%s': %s" %
                           (attr, dn, e[0]['desc']))
            self._ds = False
            raise e

    def delete_attribute(self, dn, attr, value):
        """Remove all attributes that match the value from the dn entry"""
        try:
            if not self.__dict__.has_key('_ds') or not self.__dict__['_ds']:
                self._open()
            self._ds.modify_s(dn, [(ldap.MOD_DELETE, attr, value)]) 
        except ldap.LDAPError, e:
            self.log.error("unable to remove attribute '%s' from uid '%s': %s" %
                           (attr, dn, e[0]['desc']))
            self._ds = False
            raise e

    def _open(self):
        """Open and optionnally bind a new connection to the LDAP directory"""
        try:
            if self.use_tls:
                ldap.set_option(ldap.OPT_REFERRALS, 0)
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, \
                                ldap.OPT_X_TLS_NEVER)
                protocol = 'ldaps'
            else:
                protocol = 'ldap'
            self._ds = ldap.initialize('%s://%s:%d/' % \
                                       (protocol, self.host, self.port))
            self._ds.protocol_version = ldap.VERSION3
            if self.bind:
                if not self.bind_user:
                    raise TracError("Bind enabled but credentials not defined")
                head = self.bind_user[:self.bind_user.find(',')]
                if ( head.find('=') == -1 ):
                    self.bind_user = '%s=%s' % (self.uidattr, self.bind_user)
                self._ds.simple_bind_s(self.bind_user, self.bind_passwd)
            else:
                self._ds.simple_bind_s()
        except ldap.LDAPError, e:
            self._ds = None
            if self.bind_user:
                self.log.warn("Unable to open LDAP with user %s" % \
                              self.bind_user)
            raise TracError("Unable to open LDAP cnx: %s" % e[0]['desc'])

    def _search(self, basedn, filterstr='(objectclass=*)', attributes=None, 
                scope=ldap.SCOPE_ONELEVEL):
        """Search the LDAP directory"""
        try:
            if not self.__dict__.has_key('_ds') or not self.__dict__['_ds']:
                self._open()
            sr = self._ds.search_s(basedn, scope, filterstr, attributes)
            return sr
        except ldap.NO_SUCH_OBJECT, e:
            self.log.warn("LDAP error: %s (%s)", e[0]['desc'], basedn)
            return False;    
        except ldap.LDAPError, e:
            self.log.error("LDAP error: %s", e[0]['desc'])
            self._ds = False
            return False;

    def _compare(self, dn, attribute, value):
        """Compare the attribute value of a LDAP DN"""
        try:
            if not self.__dict__.has_key('_ds') or not self.__dict__['_ds']:
                self._open()
            cr = self._ds.compare_s(dn, attribute, value)
            return cr
        except ldap.NO_SUCH_OBJECT, e:
            self.log.warn("LDAP error: %s (%s)", e[0]['desc'], dn)
            return False;    
        except ldap.LDAPError, e:
            self.log.error("LDAP error: %s", e[0]['desc'])
            self._ds = False
            return False
    
