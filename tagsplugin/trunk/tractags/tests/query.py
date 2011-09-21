# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
import doctest

import tractags.query


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(module=tractags.query))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
