# -*- coding: utf-8 -*-
#
import doctest
import unittest

from tracdependency.tests import testtracdependency

def suite():
    suite = unittest.TestSuite()
    suite.addTest(testtracdependency.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
