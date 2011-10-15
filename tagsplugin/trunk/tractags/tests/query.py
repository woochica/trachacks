# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import doctest
import unittest

import tractags.query


class QueryTestCase(unittest.TestCase):
    def test_parse(self):
        """Verify tokenization of quoted strings and strings with unary quotes.

        This as been reported as th:ticket:9057.
        """
        singlequote_phrase = r"""alpha'beta"gamma or 'alpha\'beta"gamma'"""
        q = tractags.query.Query
        self.assertEquals("""\
(or
  ("alpha'beta\"gamma")
  ("alpha'beta\"gamma"))""", repr(q(singlequote_phrase)))

        doublequote_phrase = r'alpha or "beta\'gamma\"delta" or ""'
        self.assertEquals("""\
(or
  ("alpha")
  (or
    ("beta'gamma"delta")
    ("")))""", repr(q(doublequote_phrase)))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(module=tractags.query))
    suite.addTest(unittest.makeSuite(QueryTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
