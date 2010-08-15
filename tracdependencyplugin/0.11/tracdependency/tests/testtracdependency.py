# -*- coding: utf-8 -*-

import os.path
import shutil
import tempfile
import unittest

from trac.core import *
from trac.test import EnvironmentStub, Mock
from tracdependency.tracdependency import TracDependency
from tracdependency.intertrac import InterTrac

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        self.env = EnvironmentStub(enable=['trac.*','tracusermanager.*'])
        self.env.config.set('ticket-custom', 'test', 'select') 
        self.env.path = os.path.join(self.basedir, 'trac-tempenv')
        os.mkdir(self.env.path)    

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_get_intertrac_project(self):
        tracDep = TracDependency(self.env)
        tracDep.load_intertrac_setting()
        assert tracDep.get_projects() is not None
        self.assertEqual(tracDep.get_projects(), {})

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BaseTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')


