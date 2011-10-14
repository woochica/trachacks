# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
import shutil
import tempfile

from trac.test import EnvironmentStub, Mock
from trac.perm import PermissionCache, PermissionSystem
from trac.web.href import Href

from tractags.model import TagModelProvider
from tractags.macros import TagTemplateProvider, TagWikiMacros


class TagTemplateProviderTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        TagModelProvider(self.env).environment_created()

        # TagTemplateProvider is abstract, test using a subclass
        self.tag_wm = TagWikiMacros(self.env)

    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_template_dirs_added(self):
        from trac.web.chrome import Chrome
        self.assertTrue(self.tag_wm in Chrome(self.env).template_providers)


class ListTaggedMacroTestCase(unittest.TestCase):
    
    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        TagModelProvider(self.env).environment_created()
        PermissionSystem(self.env).grant_permission('user', 'TAGS_VIEW')
        
        self.tag_twm = TagWikiMacros(self.env)
    
    def tearDown(self):
        shutil.rmtree(self.env.path)
    
    def test_empty_content(self):
        formatter = Mock(
            req = Mock(args={},
                       authname='user',
                       perm=PermissionCache(self.env, 'user'),
                       href=Href('/'),
                       abs_href='http://example.org/trac/',
                       chrome={},
            ))
        self.assertEquals('',
                str(self.tag_twm.expand_macro(formatter, 'ListTagged', '')))

class TagCloudMacroTestCase(unittest.TestCase):
    
    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        TagModelProvider(self.env).environment_created()
        
        self.tag_twm = TagWikiMacros(self.env)
    
    def tearDown(self):
        shutil.rmtree(self.env.path)
    
    def test_init(self):
        # Empty test just to confirm that setUp and tearDown works
        pass


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TagTemplateProviderTestCase, 'test'))
    suite.addTest(unittest.makeSuite(ListTaggedMacroTestCase, 'test'))
    suite.addTest(unittest.makeSuite(TagCloudMacroTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
