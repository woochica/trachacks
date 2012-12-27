# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from backlog.web_ui import BacklogModule

class BacklogRequestHandlerTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def test_something(self):
        pass

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BacklogRequestHandlerTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unitest.main(defaultTest='test_suite')
