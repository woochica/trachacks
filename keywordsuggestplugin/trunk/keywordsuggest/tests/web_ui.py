# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.test import EnvironmentStub

from keywordsuggest.web_ui import KeywordSuggestModule


class KeywordSuggestModuleTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'keywordsuggest.*'])
        self.ksm = KeywordSuggestModule(self.env)
        self.req = Mock()

    def tearDown(self):
        pass

    def test_multiplesepartor_is_default(self):
        self.assertEqual(' ', self.ksm.multiple_separator)

    def test_multipleseparator_is_empty_quotes(self):
        self.env.config.set('keywordsuggest', 'multipleseparator', "''")
        self.assertEqual(' ', self.ksm.multiple_separator)

    def test_multipleseparator_is_comma(self):
        self.env.config.set('keywordsuggest', 'multipleseparator', ',')
        self.assertEqual(',', self.ksm.multiple_separator)

    def test_multipleseparator_is_quoted_strip_quotes(self):
        self.env.config.set('keywordsuggest', 'multipleseparator', "','")
        self.assertEqual(',', self.ksm.multiple_separator)

    def test_multipleseparator_is_quoted_whitespace_strip_quotes(self):
        self.env.config.set('keywordsuggest', 'multipleseparator', "' '")
        self.assertEqual(' ', self.ksm.multiple_separator)

    def test_get_keywords_no_keywords(self): 
        self.assertEqual('', self.ksm._get_keywords_string(self.req))

    def test_get_keywords_define_in_config(self):
        self.env.config.set('keywordsuggest', 'keywords', 'tag1, tag2, tag3')
        self.assertEqual("'tag1','tag2','tag3'", self.ksm._get_keywords_string(self.req))

    def test_keywords_are_sorted(self):
        self.env.config.set('keywordsuggest', 'keywords', 'tagb, tagc, taga')
        self.assertEqual("'taga','tagb','tagc'", self.ksm._get_keywords_string(self.req))
    
    def test_keywords_duplicates_removed(self):
        self.env.config.set('keywordsuggest', 'keywords', 'tag1, tag1, tag2')
        self.assertEqual("'tag1','tag2'", self.ksm._get_keywords_string(self.req))

    def test_keywords_quoted_for_javascript(self):
        self.env.config.set('keywordsuggest', 'keywords', 'it\'s, "this"')
        self.assertEqual('\'\\"this\\"\',\'it\\\'s\'', self.ksm._get_keywords_string(self.req))

    def test_implements_irequestfilter(self):
        from trac.web.main import RequestDispatcher
        self.assertTrue(self.ksm in RequestDispatcher(self.env).filters)

    def test_implements_itemplateprovider(self):
        from trac.web.chrome import Chrome
        self.assertTrue(self.ksm in Chrome(self.env).template_providers)

    def test_implements_itemplatestreamfilter(self):
        from trac.web.chrome import Chrome
        self.assertTrue(self.ksm in Chrome(self.env).stream_filters)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(KeywordSuggestModuleTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

