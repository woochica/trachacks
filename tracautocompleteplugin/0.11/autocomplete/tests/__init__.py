import unittest

from tickettemplate.tests import test_tt

def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_tt.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
