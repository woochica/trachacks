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

from trac.perm import PermissionCache, PermissionError, PermissionSystem
from trac.test import EnvironmentStub, Mock

from crypto.api import CryptoBase
from crypto.openpgp import OpenPgpFactory


class OpenPgpFactoryTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'crypto.*'])
        self.env.path = tempfile.mkdtemp()

        self.perm = PermissionSystem(self.env)
        self.req = Mock()

        self.base = CryptoBase(self.env)
        self.factory = OpenPgpFactory(self.env)

    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_openpgp_create_key(self):
        factory = self.factory
        self.assertEqual(factory.keys(), [])
        self.assertEqual(factory.keys(private=True), [])
        key = factory.create_key(name_real='John', name_email='john@foo')
        fp = key.fingerprint
        # Check for both, private and public key.
        self.assertEqual(factory.keys(id_only=True), [fp])
        self.assertEqual(factory.keys(True, True), [fp])

    def test_openpgp_delete_key_no_perms(self):
        factory = self.factory
        key = factory.create_key()
        self.req.perm = PermissionCache(self.env)
        self.assertRaises(PermissionError, factory.delete_key,
                          key.fingerprint, self.req.perm)

    def test_openpgp_delete_key_full_perms(self):
        factory = self.factory
        key = factory.create_key()
        self.perm.grant_permission('anonymous', 'CRYPTO_DELETE')
        self.req.perm = PermissionCache(self.env)
        # Shouldn't raise an error with appropriate permission.
        factory.delete_key(key.fingerprint, self.req.perm)
        self.assertEqual(factory.keys(), [])
        self.assertEqual(factory.keys(private=True), [])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(OpenPgpFactoryTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
