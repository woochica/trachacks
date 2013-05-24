# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from unittest import TestSuite


def test_suite():
    suite = TestSuite()

    import dynfields.tests.options
    suite.addTest(dynfields.tests.options.test_suite())

    return suite
