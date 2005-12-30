
"""
Unit tests for interwiki trac plugin.
"""

import unittest

import os,sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from interwiki import *

class InterWikiLinkModuleTest(unittest.TestCase):
    def setUp(self):
        self.interwikimap = {'c2':'c2.com/', 'ww':"ww.com/"}
    def extref(self, href, text):
        t = '<a class="ext-link" href="%s"><span class="icon"></span>%s</a>'
        return t % (href, text)
    def testFormatLink(self):
        s = format_interwiki_link('link', 'c2:Foo', 'Foo', self.interwikimap)
        self.assertEquals(self.extref('c2.com/Foo', 'c2:Foo'), s)
    def testFormatLinkCustomTitle(self):
        s = format_interwiki_link('link', 'ww:Foo', 'Foo page', self.interwikimap)
        self.assertEquals(self.extref('ww.com/Foo', 'ww:Foo page'), s)
    def testFormatNonLink(self):
        s = format_interwiki_link('link', 'c3:Foo', 'link:c3:Foo', self.interwikimap)
        self.assertEquals('link:c3:Foo', s)

if __name__=='__main__':
    unittest.main()
