# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, Robert Corsaro
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.core import *
from trac.test import EnvironmentStub

from announcer.formatters.ticket import *

class TicketFormatTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub()
        self.out = TicketFormatter(self.env)

    def test_styles(self):
        self.assertTrue('text/html' in self.out.styles('email', 'ticket'))
        self.assertTrue('text/plain' in self.out.styles('email', 'ticket'))
        self.assertFalse('text/plain' in self.out.styles('email', 'wiki'))
        self.assertEqual('text/plain', self.out.alternative_style_for('email', 'ticket', 'text/blah'))
        self.assertEqual('text/plain', self.out.alternative_style_for('email', 'ticket', 'text/html'))
        self.assertEqual(None, self.out.alternative_style_for('email', 'ticket', 'text/plain'))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TicketFormatTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
