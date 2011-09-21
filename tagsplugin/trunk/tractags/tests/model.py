# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
import shutil
import tempfile

from trac.test import EnvironmentStub, Mock

from tractags.model import TagModelProvider

class TagsProviderTestCase(unittest.TestCase):
    
    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        self.tag_mp = TagModelProvider(self.env)
        self.tag_mp.environment_created()
    
    def tearDown(self):
        shutil.rmtree(self.env.path)
    
    # Helpers
    
    def _get_cursor_description(self, cursor):
        # Cursors don't look the same across Trac versions
        from trac import __version__ as trac_version
        if trac_version < '0.12':
            return cursor.description
        else:
            return cursor.cursor.description
    
    # Tests
    
    def test_table_exists(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        tags = cursor.execute("SELECT * FROM tags").fetchall()
        self.assertEquals([], tags)
        self.assertEquals(['tagspace', 'name', 'tag'],
                [col[0] for col in self._get_cursor_description(cursor)])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TagsProviderTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
