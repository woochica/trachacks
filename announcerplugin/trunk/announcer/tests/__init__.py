# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, Robert Corsaro
# Copyright (c) 2012, Steffen Hoffmann
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(announcer.api.suite())
    suite.addTest(announcer.formatter.suite())
    return suite


# Start test suite directly from command line like so:
#   $> PYTHONPATH=$PWD python tractags/tests/__init__.py
if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")
