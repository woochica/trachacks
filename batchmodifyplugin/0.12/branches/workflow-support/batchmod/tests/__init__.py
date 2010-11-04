import doctest
import unittest

import batchmod
from batchmod.tests import batchmod

def suite():
    suite = unittest.TestSuite()
    suite.addTest(batchmod.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
