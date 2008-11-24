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
import re
from RegexLink.model import *

class RegexLinkInfoTestCase(unittest.TestCase):

    def test_constructor(self):
        regex = r'\bexample\b'
        url = 'http://example.org'
        rli = RegexLinkInfo(regex, url)
        self.assertEqual(rli.regex, regex)
        self.assertEqual(rli.url, url)

    def test_replace_url_no_groups(self):
        regex = r'\bexample\d{1,3}\b'
        url = 'http://example.org'
        doc = """testdoc
            example123
            end of testdoc
        """
        rli = RegexLinkInfo(regex, url)
        match = re.search(rli.regex, doc)
        result = rli.replace_url(match)
        self.assertEquals(result, 'http://example.org')

    def test_replace_url_named_groups(self):
        regex = r'\bexample(?P<exnr>\d{1,3}):(?P<exname>[a-z]+)\b'
        url = r'http://example.org/\g<exname>/\g<exnr>'
        doc = """testdoc
            example123:test
            end of testdoc
        """
        rli = RegexLinkInfo(regex, url)
        match = re.search(rli.regex, doc)
        result = rli.replace_url(match)
        self.assertEquals(result, 'http://example.org/test/123')

if __name__ == '__main__':
    unittest.main()
