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
from trac.db import Table, Column, Index
from trac.db.api import DatabaseManager
from trac.test import EnvironmentStub, Mock

from tractags import db_default
from tractags.db import TagSetup


class TagSetupTestCase(unittest.TestCase):

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

    # Helpers

    def _get_cursor_description(self, cursor):
        # Cursors don't look the same across Trac versions
        if trac_version < '0.12':
            return cursor.description
        else:
            return cursor.cursor.description

    def _revert_tractags_schema_init(self):
        cursor = self.db.cursor()
        cursor.execute("DROP TABLE IF EXISTS tags")
        cursor.execute("DELETE FROM system WHERE name='tags_version'")
        cursor.execute("DELETE FROM permission WHERE action %s"
                       % self.db.like(), ('TAGS_%',))

    # Tests

    def test_new_install(self):
        setup = TagSetup(self.env)
        # Current tractags schema is setup with enabled component anyway.
        self._revert_tractags_schema_init()
        self.assertEquals(0, setup.get_schema_version(self.db))
        self.assertTrue(setup.environment_needs_upgrade(self.db))

        setup.upgrade_environment(self.db)
        self.assertFalse(setup.environment_needs_upgrade(self.db))
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM tags")
        tags = cursor.fetchall()
        self.assertEquals([], tags)
        self.assertEquals(['tagspace', 'name', 'tag'],
                [col[0] for col in self._get_cursor_description(cursor)])
        cursor.execute("""
            SELECT value
              FROM system
             WHERE name='tags_version'
        """)
        version = int(cursor.fetchone()[0])
        self.assertEquals(db_default.schema_version, version)

    def test_upgrade_schema_v1(self):
        # Ancient, unversioned schema - wiki only.
        schema = [
            Table('wiki_namespace')[
                Column('name'),
                Column('namespace'),
                Index(['name', 'namespace']),
            ]
        ]
        setup = TagSetup(self.env)
        # Current tractags schema is setup with enabled component anyway.
        self._revert_tractags_schema_init()

        connector = self.db_mgr._get_connector()[0]
        cursor = self.db.cursor()
        for table in schema:
            for stmt in connector.to_sql(table):
                cursor.execute(stmt)
        # Populate table with migration test data.
        cursor.execute("""
            INSERT INTO wiki_namespace
                   (name, namespace)
            VALUES ('WikiStart', 'tag')
        """)

        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM wiki_namespace")
        tags = cursor.fetchall()
        self.assertEquals([('WikiStart', 'tag')], tags)
        self.assertEquals(1, setup.get_schema_version(self.db))
        self.assertTrue(setup.environment_needs_upgrade(self.db))

        setup.upgrade_environment(self.db)
        self.assertFalse(setup.environment_needs_upgrade(self.db))
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM tags")
        tags = cursor.fetchall()
        # Db content should be migrated.
        self.assertEquals([('wiki', 'WikiStart', 'tag')], tags)
        self.assertEquals(['tagspace', 'name', 'tag'],
                [col[0] for col in self._get_cursor_description(cursor)])
        cursor.execute("""
            SELECT value
              FROM system
             WHERE name='tags_version'
        """)
        version = int(cursor.fetchone()[0])
        self.assertEquals(db_default.schema_version, version)

    def test_upgrade_schema_v2(self):
        # Just register a current, but unversioned schema.
        schema = [
            Table('tags', key=('tagspace', 'name', 'tag'))[
                Column('tagspace'),
                Column('name'),
                Column('tag'),
                Index(['tagspace', 'name']),
                Index(['tagspace', 'tag']),
            ]
        ]
        setup = TagSetup(self.env)
        # Current tractags schema is setup with enabled component anyway.
        self._revert_tractags_schema_init()

        connector = self.db_mgr._get_connector()[0]
        cursor = self.db.cursor()
        for table in schema:
            for stmt in connector.to_sql(table):
                cursor.execute(stmt)
        # Populate table with test data.
        cursor.execute("""
            INSERT INTO tags
                   (tagspace, name, tag)
            VALUES ('wiki', 'WikiStart', 'tag')
        """)

        cursor.execute("SELECT * FROM tags")
        tags = cursor.fetchall()
        self.assertEquals([('wiki', 'WikiStart', 'tag')], tags)
        self.assertEquals(2, setup.get_schema_version(self.db))
        self.assertTrue(setup.environment_needs_upgrade(self.db))

        setup.upgrade_environment(self.db)
        self.assertFalse(setup.environment_needs_upgrade(self.db))
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM tags")
        tags = cursor.fetchall()
        # Db should be unchanged.
        self.assertEquals([('wiki', 'WikiStart', 'tag')], tags)
        self.assertEquals(['tagspace', 'name', 'tag'],
                [col[0] for col in self._get_cursor_description(cursor)])
        cursor.execute("""
            SELECT value
              FROM system
             WHERE name='tags_version'
        """)
        version = int(cursor.fetchone()[0])
        self.assertEquals(db_default.schema_version, version)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TagSetupTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
