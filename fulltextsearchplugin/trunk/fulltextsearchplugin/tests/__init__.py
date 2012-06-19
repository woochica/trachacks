import unittest

import fulltextsearchplugin
from fulltextsearchplugin.tests import fulltextsearch, admin, dates

def suite():
    suite = unittest.TestSuite()
    suite.addTest(fulltextsearch.suite())
    suite.addTest(admin.suite())
    suite.addTest(dates.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
