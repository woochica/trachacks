# -*- coding: utf-8 -*-
#
# LDAP permission extension tests for Trac
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

from trac.config import Configuration
from ldapplugin.api import LdapPermissionGroupProvider,LdapPermissionStore
from trac.test import EnvironmentStub

import unittest

class LdapGroupProviderTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True)
        self.env.config.set('ldap', 'enable', 'true')
        self.env.config.set('ldap', 'basedn', 'dc=example,dc=org')
        self.env.config.set('ldap', 'host', 'localhost')

    def test_permissiongroup(self):
        gp = LdapPermissionGroupProvider(self.env)
        groups = gp.get_permission_groups('joeuser')
        assert len(groups) >= 1
        assert '@users' in groups

class LdapPermissionStoreTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True)
        self.env.config.set('ldap', 'enable', 'true')
        self.env.config.set('ldap', 'basedn', 'dc=example,dc=org')
        self.env.config.set('ldap', 'host', 'localhost')
        self.env.config.set('ldap', 'store_bind', 'true')
        self.env.config.set('ldap', 'bind_user', 'uid=trac,dc=example,dc=org')
        self.env.config.set('ldap', 'bind_passwd', 'Trac')
        self.env.config.set('ldap', 'permfilter', 'objectclass=groupofnames')
        self.action1 = 'FILE_VIEW'
        self.action2 = 'TICKET_CREATE'

    #def test_userPermissions(self):
    #    ps = LdapPermissionStore(self.env)
    #    perms = ps.get_user_permissions('@users')
    #    action = 'MILESTONE_VIEW'
    #    self.assertEqual(perms.has_key(action), True)
    #    self.assertEqual(perms[action], True)

    def test_store(self):
        self.ps = LdapPermissionStore(self.env)
        self.ps.grant_permission('@users', self.action1)
        self.ps.grant_permission('@users', self.action2)
        perms = self.ps.get_user_permissions('@users')
        self.assertEqual(perms.has_key(self.action1), True)
        self.assertEqual(perms[self.action1], True)
        self.assertEqual(perms.has_key(self.action2), True)
        self.assertEqual(perms[self.action2], True)

        self.ps = LdapPermissionStore(self.env)
        perms = self.ps.get_all_permissions()
        for perm in perms:
            print perm, "\n"

        self.ps.revoke_permission('@users', self.action1)
        perms = self.ps.get_user_permissions('@users')
        self.assertEqual(perms.has_key(self.action1), False)
        self.ps.revoke_permission('@users', self.action2)
        perms = self.ps.get_user_permissions('@users')
        self.assertEqual(perms.has_key(self.action2), False)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(LdapGroupProviderTestCase("group"))
    suite.addTest(LdapPermissionStoreTestCase("store"))
    return suite

if __name__ == '__main__':
    unittest.main()

