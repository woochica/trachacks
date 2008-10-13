import unittest

from rtadmin.tests import test_rt

def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_rt.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')