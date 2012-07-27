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

from trac.test import EnvironmentStub, Mock
from trac.web.chrome import Chrome

from crypto.web_ui import CommonTemplateProvider, UserCryptoPreferences


class CommonTemplateProviderTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'crypto.*'])
        self.env.path = tempfile.mkdtemp()

        # CommonTemplateProvider is abstract, test it using a subclass.
        self.crypto_up = UserCryptoPreferences(self.env)

    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_template_dir_added(self):
        self.assertTrue(self.crypto_up in Chrome(self.env).template_providers)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CryptoTemplateProviderTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
