import unittest

from tracwikiextras.tests import util

def suite():
    suite = unittest.TestSuite()
    suite.addTest(util.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
