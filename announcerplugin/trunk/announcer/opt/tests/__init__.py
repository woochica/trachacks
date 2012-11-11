# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, Ryan J Ollos
# Copyright (c) 2012, Steffen Hoffmann
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from announcer.opt.tests import subscribers


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(subscribers.suite())
    return suite


# Start test suite directly from command line like so:
#   $> PYTHONPATH=$PWD python announcer/opt/tests/__init__.py
if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")
