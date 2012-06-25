# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import tempfile
import unittest
from trac.wiki.tests import formatter
from trac.test import EnvironmentStub

from tracpaste.model import Paste
from tracpaste.web_ui import TracpastePlugin

"""
============================== paste: link resolver
paste:1
paste:2
------------------------------
<p>
<a class="paste" href="/paste/1" title="This is paste 1">paste:1</a>
<a class="missing paste" rel="nofollow">paste:2</a>
</p>
------------------------------
"""

def paste_setup(tc):
    paste = Paste(tc.env, title='This is paste 1')
    
class TracpastePluginTestCase(unittest.TestCase):

    def setUp(self):
        pass
        
    def test_get_link_resolvers(self):
        pass
    
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TracpastePluginTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
