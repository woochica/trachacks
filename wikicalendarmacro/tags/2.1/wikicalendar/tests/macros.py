# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Steffen Hoffmann

import shutil
import tempfile
import unittest

from trac.perm import PermissionSystem
from trac.test import EnvironmentStub, Mock
from trac.web.chrome import Chrome

from wikicalendar.macros import WikiCalendarMacros


class WikiCalendarMacrosTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*',
                                           'wikicalendar.macros.*']
        )
        self.env.path = tempfile.mkdtemp()
        self.req = Mock()

        self.db = self.env.get_db_cnx()
        self.macros = WikiCalendarMacros(self.env)

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    def test_resource_provider(self):
        self.assertTrue(self.macros in Chrome(self.env).template_providers)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(WikiCalendarMacrosTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
