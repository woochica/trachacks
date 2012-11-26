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

from trac.perm import PermissionCache, PermissionError, PermissionSystem
from trac.resource import Resource
from trac.test import EnvironmentStub, Mock

from tractags.api import TagSystem
from tractags.db import TagSetup
from tractags.wiki import WikiTagProvider


class WikiTagProviderTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        self.tag_s = TagSystem(self.env)
        self.tag_wp = WikiTagProvider(self.env)

        self.db = self.env.get_db_cnx()
        setup = TagSetup(self.env)
        # Current tractags schema is partially setup with enabled component.
        #   Revert these changes for getting a clean setup.
        self._revert_tractags_schema_init()
        setup.upgrade_environment(self.db)

        cursor = self.db.cursor()
        # Populate table with initial test data.
        cursor.execute("""
            INSERT INTO tags
                   (tagspace, name, tag)
            VALUES ('wiki', 'WikiStart', 'tag1')
        """)

        self.req = Mock()
        # Mock an anonymous request.
        self.req.perm = PermissionCache(self.env)
        self.realm = 'wiki'
        self.tags = ['tag1']

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def _revert_tractags_schema_init(self):
        cursor = self.db.cursor()
        cursor.execute("DROP TABLE IF EXISTS tags")
        cursor.execute("DELETE FROM system WHERE name='tags_version'")
        cursor.execute("DELETE FROM permission WHERE action %s"
                       % self.db.like(), ('TAGS_%',))

    # Tests

    def test_get_tags(self):
        resource = Resource('wiki', 'WikiStart')
        self.assertEquals([tag for tag in
                           self.tag_wp.get_resource_tags(self.req, resource)],
                          self.tags)

    def test_exclude_template_tags(self):
        cursor = self.db.cursor()
        # Populate table with more test data.
        cursor.execute("""
            INSERT INTO tags
                   (tagspace, name, tag)
            VALUES ('wiki', 'PageTemplates/Template', 'tag2')
        """)
        tags = ['tag1', 'tag2']
        self.assertEquals(self.tag_s.get_all_tags(self.req, '-invalid').keys(),
                          self.tags)
        self.env.config.set('tags', 'query_exclude_wiki_templates', False)
        self.assertEquals(self.tag_s.get_all_tags(self.req, '-invalid').keys(),
                          tags)

    def test_set_tags_no_perms(self):
        resource = Resource('wiki', 'TaggedPage')
        self.assertRaises(PermissionError, self.tag_wp.set_resource_tags,
                          self.req, resource, self.tags)

    def test_set_tags(self):
        resource = Resource('wiki', 'TaggedPage')
        self.req.perm = PermissionCache(self.env, username='user')
        # Shouldn't raise an error with appropriate permission.
        self.tag_wp.set_resource_tags(self.req, resource, self.tags)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(WikiTagProviderTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
