# -*- coding: utf-8 -*-
import sys
import os
import re
import unittest
from nikocale import *

class ComponentManagerStub(object):
    components = {}

    def component_activated(self, dummy):
        pass

class RequestStub(object):
    pass

class NikoCaleMacroTest(unittest.TestCase):
    def setUp(self):
        self.req = RequestStub()
        self.req.base_url = '/my-project'
        self.niko = NikoCaleMacro(ComponentManagerStub())

    def test_render(self):
        rendered = self.niko.render_macro(self.req, 'NikoCale', 'my name,10/1,(^o^),my comment')

        self.assertTrue(re.search('<td[^>]*>my name</td>', rendered, re.IGNORECASE))
        self.assertTrue(re.search('<img src="[^"]*good', rendered, re.IGNORECASE))
        self.assertTrue('title="my comment"' in rendered)
        
    def test_commas_in_comments(self):
        rendered = self.niko.render_macro(self.req, 'NikoCale', 'my name,10/1,(^o^),my comment, comma separated, does it work?')

        self.assertTrue(re.search('<td[^>]*>my name</td>', rendered, re.IGNORECASE))
        self.assertTrue(re.search('<img src="[^"]*good', rendered, re.IGNORECASE))
        self.assertTrue('title="my comment, comma separated, does it work?"' in rendered)
        
if __name__ == '__main__':
    unittest.main()

