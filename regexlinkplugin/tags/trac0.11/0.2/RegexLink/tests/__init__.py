"""
__init__.py

====================

Copyright (C) 2008 Roel Harbers

 ----------------------------------------------------------------------------
 "THE BEER-WARE LICENSE" (Revision 42):
 Roel Harbers wrote this file. As long as you retain this notice you
 can do whatever you want with this stuff. If we meet some day, and you think
 this stuff is worth it, you can buy me a beer in return.
 ----------------------------------------------------------------------------

Author:

  Roel Harbers

"""
import unittest
from RegexLink.tests.test_model import *

def suite():
    return unittest.TestSuite(map(unittest.TestLoader().loadTestsFromTestCase,
        [ RegexLinkInfoTestCase
        ]))

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
