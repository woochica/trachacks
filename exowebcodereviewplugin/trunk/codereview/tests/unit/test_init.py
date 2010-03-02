#!/bin/sh

# system imports
import unittest

# trac imports
from trac import test

# local imports
from codereview import init

class CodeReviewInitTestCase(unittest.TestCase):

    def setUp(self):
        self.env = test.EnvironmentStub()
        self.db = self.env.get_db_cnx()
        self.init = init.CodeReviewInit(self.env)
    
    def test_environment_needs_upgrade(self):
        self.init.environment_needs_upgrade(self.db)

    def test_upgrade_environment_(self):
        self.init.upgrade_environment(self.db)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CodeReviewInitTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

