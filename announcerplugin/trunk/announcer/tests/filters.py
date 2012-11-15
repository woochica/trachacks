# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, Ryan J Ollos
# Copyright (c) 2012, Steffen Hoffmann
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.test import EnvironmentStub

from announcer.filters import DefaultPermissionFilter


class DefaultPermissionFilterTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'announcer.filters.*'])
        self.env.path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_init(self):
        # Test just to confirm that DefaultPermissionFilter initializes cleanly
        #   and that setUp and tearDown both work.
        DefaultPermissionFilter(self.env)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DefaultPermissionFilterTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
