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
        # Initialize default (SQLite) db in memory.
        self.db_mgr = DatabaseManager(self.env)
        # Workaround required for Trac 0.11 up to 0.12.4 .
        if trac_version < '0.13dev':
            self.db_mgr.init_db()
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

    # Tests

    def test_new_install(self):
        setup = TagSetup(self.env)
        self.assertEquals(0, setup.get_schema_version(self.db))

        setup.upgrade_environment(self.db)
        cursor = self.db.cursor()
        tags = cursor.execute("SELECT * FROM tags").fetchall()
        self.assertEquals([], tags)
        self.assertEquals(['tagspace', 'name', 'tag'],
                [col[0] for col in self._get_cursor_description(cursor)])
        version = cursor.execute("""
                      SELECT value
                        FROM system
                       WHERE name='tags_version'
                  """).fetchone()
        self.assertEquals(db_default.schema_version, int(version[0]))

    def test_upgrade_schema_v1(self):
        # Ancient, unversioned schema - wiki only.
        schema = [
            Table('wiki_namespace')[
                Column('name'),
                Column('namespace'),
                Index(['name', 'namespace']),
            ]
        ]
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
        # Current tractags schema is setup with enabled component anyway.
        cursor.execute("DROP TABLE IF EXISTS tags")

        tags = cursor.execute("SELECT * FROM wiki_namespace").fetchall()
        self.assertEquals([('WikiStart', 'tag')], tags)
        setup = TagSetup(self.env)
        self.assertEquals(1, setup.get_schema_version(self.db))

        setup.upgrade_environment(self.db)
        cursor = self.db.cursor()
        tags = cursor.execute("SELECT * FROM tags").fetchall()
        # Db content should be migrated.
        self.assertEquals([('wiki', 'WikiStart', 'tag')], tags)
        self.assertEquals(['tagspace', 'name', 'tag'],
                [col[0] for col in self._get_cursor_description(cursor)])
        version = cursor.execute("""
                      SELECT value
                        FROM system
                       WHERE name='tags_version'
                  """).fetchone()
        self.assertEquals(db_default.schema_version, int(version[0]))

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
        connector = self.db_mgr._get_connector()[0]
        cursor = self.db.cursor()
        # Current tractags schema is setup with enabled component anyway.
        cursor.execute("DROP TABLE IF EXISTS tags")

        for table in schema:
            for stmt in connector.to_sql(table):
                cursor.execute(stmt)
        # Populate table with test data.
        cursor.execute("""
            INSERT INTO tags
                   (tagspace, name, tag)
            VALUES ('wiki', 'WikiStart', 'tag')
        """)

        tags = cursor.execute("SELECT * FROM tags").fetchall()
        self.assertEquals([('wiki', 'WikiStart', 'tag')], tags)
        setup = TagSetup(self.env)
        self.assertEquals(2, setup.get_schema_version(self.db))

        setup.upgrade_environment(self.db)
        cursor = self.db.cursor()
        tags = cursor.execute("SELECT * FROM tags").fetchall()
        # Db should be unchanged.
        self.assertEquals([('wiki', 'WikiStart', 'tag')], tags)
        self.assertEquals(['tagspace', 'name', 'tag'],
                [col[0] for col in self._get_cursor_description(cursor)])
        version = cursor.execute("""
                      SELECT value
                        FROM system
                       WHERE name='tags_version'
                  """).fetchone()
        self.assertEquals(db_default.schema_version, int(version[0]))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TagSetupTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
