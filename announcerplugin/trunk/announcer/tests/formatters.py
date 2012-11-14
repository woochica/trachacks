# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, Robert Corsaro
# Copyright (c) 2012, Steffen Hoffmann
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.test import EnvironmentStub

from announcer.formatters import TicketFormatter, WikiFormatter


class TicketFormatterTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub()
        self.out = TicketFormatter(self.env)

    # Tests

    def test_styles(self):
        self.assertTrue('text/html' in self.out.styles('email', 'ticket'))
        self.assertTrue('text/plain' in self.out.styles('email', 'ticket'))
        self.assertFalse('text/plain' in self.out.styles('email', 'wiki'))
        self.assertEqual('text/plain',
                         self.out.alternative_style_for('email', 'ticket',
                                                        'text/blah'))
        self.assertEqual('text/plain',
                         self.out.alternative_style_for('email', 'ticket',
                                                        'text/html'))
        self.assertEqual(None,
                         self.out.alternative_style_for('email', 'ticket',
                                                        'text/plain'))


class WikiFormatterTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub()
        self.out = WikiFormatter(self.env)

    # Tests

    def test_styles(self):
        # HMTL format for email notifications is yet unsupported for wiki.
        #self.assertTrue('text/html' in self.out.styles('email', 'wiki'))
        self.assertTrue('text/plain' in self.out.styles('email', 'wiki'))
        self.assertFalse('text/plain' in self.out.styles('email', 'ticket'))
        self.assertEqual('text/plain',
                         self.out.alternative_style_for('email', 'wiki',
                                                        'text/blah'))
        self.assertEqual('text/plain',
                         self.out.alternative_style_for('email', 'wiki',
                                                        'text/html'))
        self.assertEqual(None,
                         self.out.alternative_style_for('email', 'wiki',
                                                        'text/plain'))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TicketFormatterTestCase, 'test'))
    suite.addTest(unittest.makeSuite(WikiFormatterTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
