# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from unittest import TestSuite

def test_suite():
    suite = TestSuite()
    
    import backlog.tests.web_ui
    suite.addTest(backlog.tests.web_ui.test_suite())
    
    return suite
