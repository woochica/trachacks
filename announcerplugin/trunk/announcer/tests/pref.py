# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, Steffen Hoffmann
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.db.api import DatabaseManager
from trac.test import EnvironmentStub
from trac.web.chrome import Chrome

from announcer.pref import AnnouncerTemplateProvider
from announcer.pref import AnnouncerPreferences
from announcer.pref import SubscriptionManagementPanel


class AnnouncerPreferencesTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*'])
        self.env.path = tempfile.mkdtemp()
        self.db_mgr = DatabaseManager(self.env)
        self.db = self.env.get_db_cnx()

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Tests

    def test_init(self):
        # Test just to confirm that IPreferencePanelProviders initialize
        #   cleanly and that setUp and tearDown both work.
        AnnouncerPreferences(self.env)
        SubscriptionManagementPanel(self.env)
        pass


class AnnouncerTemplateProviderTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'announcer.pref.*'])
        self.env.path = tempfile.mkdtemp()

        # AnnouncerTemplateProvider is abstract, test using a subclass.
        self.sm_panel = SubscriptionManagementPanel(self.env)

    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_template_dirs_added(self):
        self.assertTrue(self.sm_panel in Chrome(self.env).template_providers)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AnnouncerPreferencesTestCase, 'test'))
    suite.addTest(unittest.makeSuite(AnnouncerTemplateProviderTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
