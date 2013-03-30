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
    suite = unittest.TestSuite()
    suite.addTest(macros.suite())
    return suite


# Start test suite directly from command line like so:
#   $> PYTHONPATH=$PWD python wikicalendar/tests/__init__.py
if __name__ == '__main__':
    unittest.main(defaultTest='suite')
