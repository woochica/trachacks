# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.test import EnvironmentStub, Mock
from trac.perm import PermissionCache, PermissionSystem
from trac.web.href import Href

from tractags.macros import TagTemplateProvider, TagWikiMacros


class TagTemplateProviderTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()

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

        self.tag_twm = TagWikiMacros(self.env)

    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_empty_content(self):
        req = Mock(path_info='/wiki/ListTaggedPage',
                   args={},
                   authname='user',
                   perm=PermissionCache(self.env, 'user'),
                   href=Href('/'),
                   abs_href='http://example.org/trac/',
                   chrome={},
                   session={},
                   locale='',
                   tz=''
            )
        context = Mock(env=self.env, href=Href('/'), req=req)
        formatter = Mock(context=context, req=req)
        self.assertTrue('No resources found' in
                        str(self.tag_twm.expand_macro(formatter,
                                                      'ListTagged', '')))


class TagCloudMacroTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()

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
