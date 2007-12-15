import doctest
import unittest

def suite():
    from acct_mgrtests import htfile, db
    suite = unittest.TestSuite()
    suite.addTest(htfile.suite())
    suite.addTest(db.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
