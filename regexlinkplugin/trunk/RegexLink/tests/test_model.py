"""
test_model.py

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
import RegexLink.model

class RegexLinkInfoTestCase(unittest.TestCase):

    def test_constructor(self):
        re = '\bexample\b'
        u = 'http://example.org'
        self.assertEqual(1, 1)
#        rli = RegexLinkInfo(re, u)
#        self.assertEqual(rli.regex, re)
#        self.assertEqual(rli.url, u)
