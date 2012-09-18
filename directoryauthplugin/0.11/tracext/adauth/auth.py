# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>

from trac.core import *
from trac.config import Option

import ldap
import time

from acct_mgr.api import IPasswordStore
from tracext.adauth.api import IPermissionUserProvider

__all__ = ['ADAuthStore']

class ADAuthStore(Component):
    """AD Password Store for Account Manager """

    implements(IPasswordStore, IPermissionUserProvider)

    ads = Option('account-manager', 'ad_server', 'localhost', 'Address of the Active Directory Server')
    base_dn = Option('account-manager', 'base_dn', None, 'Base DN used for account searches')
    bind_dn = Option('account-manager', 'bind_dn', None, 'DN used to bind to Active Directory')
    bind_pw = Option('account-manager', 'bind_passwd', None, 'Password used when binding to Active Directory')
    auth_group = Option('account-manager', 'auth_group', None, 'DN of group containing valid users. If None, any AD user is valid')
    admin_group = Option('account-manager', 'admin_group', None, 'DN of group containing TRAC_ADMIN users')


    # IPasswordStore
    def config_key(self):
        """Deprecated"""

    def get_users(self, populate_session=True):
        """Grab a list of users from Active Directory"""
        lcnx = self._bind_ad()
        if lcnx:
            if self.auth_group:
                userinfo = self.expand_group_users(lcnx, self.auth_group)
            else:
                users = lcnx.search_s(self.base_dn, ldap.SCOPE_SUBTREE,
                                      "objectCategory=person",
                                      ['sAMAccountName', 'mail',
                                       'proxyAddresses', 'displayName'])
                userinfo = [self._get_userinfo(u[1]) for u in users]
        else:
            raise TracError('Unable to bind to Active Directory')
        if populate_session:
            self._populate_user_session(userinfo)
        return [u[0] for u in userinfo]

    def expand_group_users(self, cnx, group):
        """Given a group name, enumerate all members"""
        g = cnx.search_s(group, ldap.SCOPE_BASE, attrlist=['member'])
        if g and g[0][1].has_key('member'):
            users = []
            for m in g[0][1]['member']:
                e = cnx.search_s(m, ldap.SCOPE_BASE)
                if e:
                    if 'person' in e[0][1]['objectClass']:
                        users.append(self._get_userinfo(e[0][1]))
                    elif 'group' in e[0][1]['objectClass']:
                        users.extend(self.expand_group_users(cnx, e[0][0]))
                    else:
                        self.log.debug('The group member (%s) is neither a group nor a person' % e[0][0])
                else:
                    self.log.debug('Unable to find user listed in group: %s' % str(m))
                    self.log.debug('This is very strange and you should probably check '
                                   'the consistency of your LDAP directory.' % str(m))
            return users
        else:
            self.log.debug('Unable to find any members of the group %s' % group)
            return []

    def has_user(self, user):
        users = self.get_users()
        return user.lower() in users

    def check_password(self, user, password):
        """Checks the password against LDAP"""
        dn = self._get_user_dn(user)
        success = None
        msg = "User Login: %s" % str(user)
        if dn:
            success = self._bind_ad(dn, password) or False
        if success:
            msg += " Password Verified"
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

        cnx = self._bind_ad()
        if cnx and self.admin_group:
            users = [u[0] for u in self.expand_group_users(cnx, self.admin_group)]
            if username in users:
                return ['TRAC_ADMIN']
        return []

    # Internal methods
    def _bind_ad(self, user_dn=None, passwd=None):
        user = user_dn or self.bind_dn
        password = passwd or self.bind_pw

        if not self.ads.lower().startswith('ldap://'):
            ads = 'ldap://%s' % self.ads
        else:
            ads = self.ads

        try:
            l = ldap.initialize(ads)
        except:
            raise TracError('Unable to contact Active Directory >>>%s<<<' % ads)

        if not user:
            raise TracError('The bind_dn ini option must be set')
        if not password:
            raise TracError('The bind_pw ini option must be set')

        try:
            l.simple_bind_s(user, password)
        except Exception, e:
            self.log.debug('Unable to bind to Active Directory', exc_info=e)
            return None 
        return l

    def _get_user_dn(self, user):
        if self.has_user(user):
            lcnx = self._bind_ad()
            if lcnx:
                try:
                    u = lcnx.search_s(self.base_dn, ldap.SCOPE_SUBTREE, "(&(objectCategory=person)(sAMAccountName=%s))" % user, ['sAMAccountName'])
                    return u[0][0]
                except Exception, e:
                    self.log.debug('user not found: %s' % user, exc_info=e)
                    return None
            else:
                raise TracError('Unable to bind to Active Directory')
        return None

    def _get_userinfo(self, attrs):
        """ Extract the userinfo tuple from the LDAP search result """
        username = attrs['sAMAccountName'][0].lower()
        displayname = attrs.get('displayName', [''])[0]
        email = ''
        if 'mail' in attrs:
            email = attrs['mail'][0].lower()
        elif 'proxyAddresses' in attrs:
            for e in attrs['proxyAddress']:
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
        cnx = self.env.get_db_cnx()
        lastvisit = int(time.time())
        for uname, displayname, email in userinfo:
            try:
                cur = cnx.cursor()
                cur.execute('INSERT INTO session (sid, authenticated, '
                            'last_visit) VALUES (%s, 1, %s)',
                            (uname, lastvisit))
                cnx.commit()
            except:
                cnx.rollback()
            if email:
                try:
                    cur = cnx.cursor()
                    cur.execute("INSERT INTO session_attribute"
                                "    (sid, authenticated, name, value)"
                                " VALUES (%s, 1, 'email', %s)",
                                (uname, email))
                    cnx.commit()
                except:
                    cnx.rollback()
            if displayname:
                try:
                    cur = cnx.cursor()
                    cur.execute("INSERT INTO session_attribute"
                                "    (sid, authenticated, name, value)"
                                " VALUES (%s, 1, 'name', %s)",
                                (uname, displayname))
                    cnx.commit()
                except:
                    cnx.rollback()
            continue
        cnx.close()
