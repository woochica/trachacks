# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from unittest import TestSuite

def test_suite():
    suite = TestSuite()
    
    import tracpaste.tests.wikisyntax
    suite.addTest(tracpaste.tests.wikisyntax.test_suite())
    
    return suite