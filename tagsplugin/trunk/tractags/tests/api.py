# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac import __version__ as trac_version
from trac.db.api import DatabaseManager
from trac.perm import PermissionCache, PermissionError, PermissionSystem
from trac.resource import Resource
from trac.test import EnvironmentStub, Mock

from tractags.api import TagSystem
from tractags.db import TagSetup


class TagSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        # Workaround required for Trac 0.11 up to 0.12.4 .
        #   Initialize default (SQLite) db in memory.
        if trac_version < '0.13dev':
            DatabaseManager(self.env).init_db()
        self.perms = PermissionSystem(self.env)
        self.req = Mock()

        self.actions = ['TAGS_ADMIN', 'TAGS_MODIFY', 'TAGS_VIEW']
        self.tag_s = TagSystem(self.env)
        self.db = self.env.get_db_cnx()
        setup = TagSetup(self.env)
        setup.upgrade_environment(self.db)

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    def test_available_actions(self):
        for action in self.actions:
            self.failIf(action not in self.perms.get_actions())

    def test_set_tags_no_perms(self):
        resource = Resource('wiki', 'WikiStart')
        tags = ['tag1']
        self.req.perm = PermissionCache(self.env)
        self.assertRaises(PermissionError, self.tag_s.set_tags, self.req,
                          resource, tags)

    def test_set_tags(self):
        resource = Resource('wiki', 'WikiStart')
        tags = ['tag1']
        self.req.perm = PermissionCache(self.env, username='authenticated')
        # Shouldn't raise an error with appropriate permission.
        self.tag_s.set_tags(self.req, resource, tags)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TagSystemTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
