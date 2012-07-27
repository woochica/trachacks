#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import shutil
import tempfile
import unittest

from trac.perm import PermissionSystem
from trac.test import EnvironmentStub, Mock

from crypto.admin import CryptoAdminPanel


class CryptoAdminPanelTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'crypto.*'])
        self.env.path = tempfile.mkdtemp()
        self.perm = PermissionSystem(self.env)
        self.req = Mock()

        self.crypto_ap = CryptoAdminPanel(self.env)

    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_available_actions(self):
        self.failIf('CRYPTO_ADMIN' not in self.perm.get_actions())
        self.failIf('CRYPTO_DELETE' not in self.perm.get_actions())

    def test_available_actions_no_perms(self):
        self.perm.grant_permission('admin', 'authenticated')
        self.assertFalse(self.perm.check_permission('CRYPTO_ADMIN', 'admin'))
        self.assertFalse(self.perm.check_permission('CRYPTO_DELETE', 'admin'))

    def test_available_actions_delete_only(self):
        self.perm.grant_permission('admin', 'CRYPTO_DELETE')
        self.assertFalse(self.perm.check_permission('CRYPTO_ADMIN', 'admin'))
        self.assertTrue(self.perm.check_permission('CRYPTO_DELETE', 'admin'))

    def test_available_actions_full_perms(self):
        self.perm.grant_permission('admin', 'TRAC_ADMIN')
        self.assertTrue(self.perm.check_permission('CRYPTO_ADMIN', 'admin'))
        self.assertTrue(self.perm.check_permission('CRYPTO_DELETE', 'admin'))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CryptoAdminPanelTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
