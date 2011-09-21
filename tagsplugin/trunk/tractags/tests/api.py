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
from tractags.api import TagSystem


class TagSystemTestCase(unittest.TestCase):
    
    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        TagModelProvider(self.env).environment_created()
        
        self.tag_s = TagSystem(self.env)
    
    def tearDown(self):
        shutil.rmtree(self.env.path)
    
    def test_init(self):
        # Empty test just to confirm that setUp and tearDown works
        pass


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TagSystemTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
