# -*- coding: utf-8 -*-
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest


def suite():
    from mastertickets.tests import model
    suite = unittest.TestSuite()
    suite.addTest(model.suite())
    return suite


# Start test suite directly from command line like so:
#   $> PYTHONPATH=$PWD python tracvote/tests/__init__.py
if __name__ == '__main__':
    unittest.main(defaultTest='suite')
