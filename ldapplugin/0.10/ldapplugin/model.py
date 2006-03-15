# -*- coding: iso-8859-1 -*-
#
# LDAP permission extensions for Trac
# 
# Copyright (C) 2003-2005 Edgewall Software
# Copyright (C) 2005 Emmanuel Blot <manu.blot@gmail.com>
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
from trac.perm import IPermissionGroupProvider,IPermissionStore

LDAP_MODULE_CONFIG = [ 'enable', 'permattr', 'permfilter',
                       'global_perms', 'cache_ttl', 'cache_size',
                       'group_bind', 'group_user', 'group_passwd',
                       'store_bind', 'store_user', 'store_passwd' ]

LDAP_DIRECTORY_PARAMS = [ 'host', 'port',
                          'basedn', 'user_basedn', 'group_basedn',
                          'groupname', 'groupmember',
                          'groupattr', 'uidattr']

class LdapPermissionGroupProvider(Component):
    """
    Provides permission groups from a LDAP directory
    """
    implements(IPermissionGroupProvider)

    def __init__(self):
        # looks for groups only if LDAP support is enabled
        self.enabled = self.config.getbool('ldap', 'enable')
        if not self.enabled:
            return
        # LDAP connection
        self._ldap = None
        # user entry local cache
        self._cache = {}
        # max time to live for a cache entry
        self._cache_ttl = int(self.env.config.get('ldap', 'cache_ttl', str(15*60)))
        # max cache entries
        self._cache_size = min(25, int(self.env.config.get('ldap', 'cache_size', '100')))

    # IPermissionProvider interface

    def get_permission_groups(self, username):
        groups = ['anonymous']
        if username and username != 'anonymous':
            groups.append('authenticated')

        if self.enabled:
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
                    self.env.log.debug('cached: ' + ','.join(groups))
                    return groups

            # cache miss (either not found or too old)
            if not self._ldap:
                # there is no LDAP connection, creates a new one
                params = {}
                # uses the ldap config parameters
                for name,value in self.env.config.options('ldap'):
                    if name in LDAP_DIRECTORY_PARAMS:
                        params[name] = value
                # new LDAP connection
                self._ldap = LdapConnection(self.env.log, **params)
                if self.env.config.getbool('ldap', 'group_bind'): 
                    u = self.env.config.get('ldap', 'group_user')
                    p = self.env.config.get('ldap', 'group_passwd')
                    self._ldap.set_credentials(u, p)

            # retrieves the user groups from LDAP
            ldapgroups = self._ldap.get_user_groups(username)
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
            self.env.log.debug('new: ' + ','.join(groups))
            groups.extend(ldapgroups)

        return groups


class LdapPermissionStore(Component):
    """
    Stores and manages permissions with a LDAP directory backend
    """
    implements(IPermissionStore)

    group_providers = ExtensionPoint(IPermissionGroupProvider)

    def __init__(self):
        # looks for groups only if LDAP support is enabled
        self.enabled = self.config.getbool('ldap', 'enable')
        if not self.enabled:
            return
        # LDAP connection
        self._ldap = None
        self._permattr = self.env.config.get('ldap', 'permattr', 'tracperm')
        # regular expression
        self._re = re.compile('^(.+?)=(.+?),(.+)$')
        # user entry local cache
        self._cache = {}
        # max time to live for a cache entry
        self._cache_ttl = int(self.env.config.get('ldap', 'cache_ttl', str(15*60)))
        # max cache entries
        self._cache_size = min(25, int(self.env.config.get('ldap', 'cache_size', '100')))
        # environment name
        envpath = self.env.path.replace('\\','/')
        self.env_name = envpath[1+envpath.rfind('/'):]
        # use directory-wide permissions
        self.global_perms = self.config.getbool('ldap', 'global_perms')

    # IPermissionStore interface

    def get_user_permissions(self, username):
        self.env.log.debug('get_user_permissions ' + username)

        if not self.enabled:
            raise TracError("LdapPermissionStore is disabled")
        actions = []
        current_time = time.time()

        if username in self._cache:
            lut, actions = self._cache[username]
            if current_time < lut+self._cache_ttl:
                self.env.log.debug('cached: ' + ','.join(actions))
        else:
            users = [username]
            for provider in self.group_providers:
                users += list(provider.get_permission_groups(username))
        
            for user in users:
                for action in self._get_permissions(self._create_uid(user)):
                    if action not in actions:
                        actions.append(action)

            if len(actions) > 0:
                if len(self._cache) >= self._cache_size:
                    cache_keys = self._cache.keys()
                    cache_keys.sort(lambda x,y: cmp(self._cache[x][0], 
                                                    self._cache[y][0]))
                    old_keys = cache_keys[:(5*self._cache_size)/100]
                    for k in old_keys:
                        del self._cache[k]
            else:
                if username in self._cache:
                    del self._cache[username]

            self.env.log.debug('new: %s' % actions)
            self._cache[username] = [current_time, actions]

        perms = {}
        for action in actions: 
                perms[action] = True
        return perms

    def get_all_permissions(self):
        self.env.log.debug('get_all_permissions')
        if not self.enabled:
            raise TracError("LdapPermissionStore is disabled")
        if not self._ldap:
            self._openldap()
        perms = []
        dns = self._ldap.get_dn(self.env.config.get('ldap', 'permfilter',
                                                    'objectclass=*'))
        basedn = self.env.config.get('ldap','basedn','')
        for dn in dns:
            m = self._re.search(dn)
            user = None
            if m:
                if m.group(3).lower() == basedn.lower():
                    if m.group(1).lower() == \
                      self.env.config.get('ldap', 'groupattr', 'cn'):
                        user = "@%s" % m.group(2)
                        dn = "%s=%s" % (m.group(1),m.group(2))
                    elif m.group(1).lower() == \
                      self.env.config.get('ldap', 'uidattr', 'uid'):
                        user = m.group(2)
                        dn = "%s=%s" % (m.group(1),m.group(2))
                    else:
                        continue
            actions = self._ldap.get_attribute(dn, self._permattr)
            for action in actions:
                xaction = self._extract_action(action)
                if not xaction:
                    continue
                perms.append((user, xaction))
        return perms

    def grant_permission(self, username, action):
        self.env.log.debug('grant_permission %s: %s' % (username, action))
        if not self.enabled:
            raise TracError("LdapPermissionStore is disabled")
        if not self._ldap:
            self._openldap()
        uid = self._create_uid(username)
        try:
            permlist = self._get_permissions(uid)
            if action not in permlist:
                xaction = self._build_action(action)        
                self._ldap.add_attribute(uid, self._permattr, xaction)
        except ldap.LDAPError, e:
            raise TracError, "Unable to grant permission %s to %s: %s" \
                             % (action, username, e[0]['desc'])

    def revoke_permission(self, username, action):
        self.env.log.debug('revoke_permission %s: %s' % (username, action))
        if not self.enabled:
            raise TracError("LdapPermissionStore is disabled")
        if not self._ldap:
            self._openldap()
        uid = self._create_uid(username)
        try:
            permlist = self._get_permissions(uid)
            if action in permlist:
                xaction = self._build_action(action)
                self._ldap.delete_attribute(uid, self._permattr, xaction)
        except ldap.LDAPError, e:
            raise TracError, "Unable to revoke permission %s to %s: %s" \
                             % (action, username, e[0]['desc'])

    # Private implementation

    def _openldap(self):
        # there is no LDAP connection, creates a new one
        params = {}
        # uses the ldap config parameters
        for name,value in self.env.config.options('ldap'):
            if name not in LDAP_MODULE_CONFIG:
                params[name] = value
        # new LDAP connection
        self._ldap = LdapConnection(self.env.log, **params)
        if self.config.getbool('ldap', 'store_bind'):
            u = self.env.config.get('ldap', 'store_user')
            p = self.env.config.get('ldap', 'store_passwd')
            self._ldap.set_credentials(u, p)

    def _create_uid(self, username):
        prefix = None
        if username.startswith('@'):
            prefix = self.env.config.get('ldap', 'groupattr', 'cn')
            return '%s=%s' % (prefix, username[1:])
        else:
            prefix = self.env.config.get('ldap', 'uidattr', 'uid')
            return '%s=%s' % (prefix, username)

    def _get_permissions(self, uid):
        if not self._ldap:
            self._openldap()
        actions = self._ldap.get_attribute(uid, self._permattr) 
        perms = []
        for action in actions:
            if action not in perms:
                xaction = self._extract_action(action)
                if xaction:
                    perms.append(xaction)
        return perms

    def _extract_action(self, action):
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
        if self.global_perms:
            return action
        return "%s:%s" % (self.env_name, action)

class LdapConnection(object):
    """
    Wrapper to the LDAP directory
    Uses only synchronous LDAP calls
    """
    def __init__(self, log, **ldap):
        self.log = log
        self.host = 'localhost'
        self.port = 389
        self.basedn = ''
        self.user_basedn = None
        self.group_basedn = None
        self.groupname = 'groupofnames'
        self.groupmember = 'member'
        self.groupattr = 'cn'
        self.uidattr = 'uid'
        for key in ldap.keys():
            self.__setattr__(key, ldap[key])
        if not self.user_basedn:
            self.user_basedn = self.basedn
        if not self.group_basedn:
            self.group_basedn = self.basedn
        if not isinstance(self.port, int):
            self.port = int(self.port)
        self._uid = None
        self._password = None

    def basedn(self):
        return self.basedn

    def user_basedn(self):
        return self.user_basedn

    def group_basedn(self):
        return self.group_basedn

    def set_credentials(self, uid, password):
        self._uid = uid
        self._password = password
    
    def close(self):
        self._ds.unbind_s()
        self._ds = None
        self._uid = ''
        self._passwd = ''

    def isOwner(self, uid):
        return self._uid == uid

    def _open(self):
        try:
            self._ds = ldap.initialize('ldap://%s:%d/' % (self.host, self.port))
            self._ds.protocol_version = ldap.VERSION3
            if self._uid is not None:
                if ( self._uid.find('=') == -1 ):
                    self._uid = '%s=%s' % (self.uidattr, self._uid)
                self._ds.simple_bind_s(self._uid + ',' + self.basedn, 
                                       self._password)
            else:
                self._ds.simple_bind_s()

        except ldap.LDAPError, e:
            self._ds = None
            raise TracError("Unable to open LDAP connection: %s" % e[0]['desc'])

    def _search(self, filter, attributes=None):
        try:
            if not self.__dict__.has_key('_ds') or not self.__dict__['_ds']:
                self._open()
            sr = self._ds.search_s(self.basedn, ldap.SCOPE_SUBTREE, 
                                   filter, attributes)
            return sr

        except ldap.LDAPError, e:
            self._ds = False
            return False;
        
    def _compare(self, dn, attribute, value):
        try:
            if not self.__dict__.has_key('_ds') or not self.__dict__['_ds']:
                self._open()
            cr = self._ds.compare_s(dn, attribute, value)
            return cr
        
        except ldap.LDAPError, e:
            self._ds = False
            return False

    def enumerate_groups(self):
        attributes = ['dn']
        groups = []
        for attempt in range(2):
            sr = self._search('objectclass=' + self.groupname, attributes)
            if sr:
                for (dn, attrs) in sr:
                    regex = re.compile('^(\w+)=(\w+)')
                    m = regex.search(dn)
                    if m:
                        groups.append(m.group(2))
                break
            if self._ds:
                break
        return groups
    
    def is_in_group(self, uid, group):
        dn = '%s=%s,%s' % (self.groupattr, group, self.group_basedn)
        value = '%s=%s,%s' % (self.uidattr, uid, self.user_basedn)
        for attempt in range(2):
            cr = self._compare(dn, self.groupmember, value)
            if self._ds:
                return cr
        return False

    def get_dn(self, filter):
        dns = []
        for attempt in range(2):
            sr = self._search(filter, ['dn'])
            if sr:
                for (dn, attrs) in sr:
                    dns.append(dn)
                break
            if self._ds:
                break
        return dns
    
    def get_uid(self, filter):
        uids = []
        for attempt in range(2):
            sr = self._search(filter, ['dn'])
            if sr:
                for (dn, attrs) in sr:
                    regex = re.compile('^(\w+)=(\w+)')
                    m = regex.search(dn)
                    if m:
                        uids.append(m.group(2))
                break
            if self._ds:
                break
        return uids

    def get_user_groups(self, username):
        ldap_groups = self.enumerate_groups()
        groups = []
        for group in ldap_groups:
            if self.is_in_group(username, group):
                groups.append('@' + group)
        return groups

    def get_attribute(self, uid, attr):
        attributes = [ attr ]
        values = []
        for attempt in range(2):
            sr = self._search(uid, attributes)
            if sr:
                for (dn, attrs) in sr:
                    if attrs.has_key(attr):
                        values = attrs[attr]
                break
            if self._ds:
                break
        return values

    def add_attribute(self, uid, attr, value):
        try:
            if not self.__dict__.has_key('_ds') or not self.__dict__['_ds']:
                self._open()
            dn = "%s,%s" % (uid, self.basedn)
            self._ds.modify_s(dn, [(ldap.MOD_ADD, attr, value)]) 

        except ldap.LDAPError, e:
            self.log.error("unable to add attribute '%s' to uid '%s': %s" %
                           (attr, uid, e[0]['desc']))
            self._ds = False
            raise e

    def delete_attribute(self, uid, attr, value):
        try:
            if not self.__dict__.has_key('_ds') or not self.__dict__['_ds']:
                self._open()
            dn = "%s,%s" % (uid, self.basedn)
            self._ds.modify_s(dn, [(ldap.MOD_DELETE, attr, value)]) 

        except ldap.LDAPError, e:
            self.log.error("unable to remove attribute '%s' from uid '%s': %s" %
                           (attr, uid, e[0]['desc']))
            self._ds = False
            raise e

