# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, Robert Corsaro
# Copyright (c) 2012, Ryan J Ollos
# Copyright (c) 2012, Steffen Hoffmann
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from announcer.tests import api, filters, formatters, model, pref, subscribers
from announcer.opt.tests import test_suite as opt_test_suite


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(api.suite())
    suite.addTest(filters.suite())
    suite.addTest(formatters.suite())
    suite.addTest(model.suite())
    suite.addTest(pref.suite())
    suite.addTest(subscribers.suite())

    suite.addTest(opt_test_suite())

    return suite


# Start test suite directly from command line like so:
#   $> PYTHONPATH=$PWD python announcer/tests/__init__.py
if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")
