# -*- coding: utf-8 -*-

import unittest

from tracautowikify.tests import autowikify


def suite():
    suite = unittest.TestSuite()
    suite.addTest(autowikify.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
