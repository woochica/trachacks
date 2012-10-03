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

    def test_implements_itemplateprovider(self):
        from trac.web.chrome import Chrome
        self.assertTrue(self.ksm in Chrome(self.env).template_providers)

    def test_implements_irequestfilter(self):
        from trac.web.main import RequestDispatcher
        self.assertTrue(self.ksm in RequestDispatcher(self.env).filters)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(KeywordSuggestModuleTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

