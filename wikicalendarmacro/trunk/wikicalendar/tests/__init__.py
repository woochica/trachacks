# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Steffen Hoffmann

import unittest


def suite():
    from wikicalendar.tests import macros
    test_suite = unittest.TestSuite()
    test_suite.addTest(macros.suite())
    return test_suite


# Start test suite directly from command line like so:
#   $> PYTHONPATH=$PWD python wikicalendar/tests/__init__.py
if __name__ == '__main__':
    unittest.main(defaultTest='suite')
