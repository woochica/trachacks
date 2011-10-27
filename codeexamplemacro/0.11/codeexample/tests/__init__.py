import unittest
from codeexample.tests import test_all


def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_all.suite())
    return suite
