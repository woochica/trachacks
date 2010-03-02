#!/usr/bin/python

# system imports
import unittest

# trac imports
import trac

class TracTestCase(unittest.TestCase):

    def test_trac(self):
        self.failUnless(trac.__version__.find('0.10') >= 0)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TracTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main()
