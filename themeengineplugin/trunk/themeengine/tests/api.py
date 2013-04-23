# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2020 Olemis Lang <olemis@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""Tests for the TracThemeEngine API"""
import unittest

from trac.test import EnvironmentStub

from themeengine.api import ThemeEngineSystem

class ThemeSystemTestCase(unittest.TestCase):
    """Unit tests covering the theme system API
    """
    def setUp(self):
        self.env = env = EnvironmentStub(enable=['trac.*', 'themeengine.*'])
        self.themesys = ThemeEngineSystem(env)
        env.config.set('theme', 'theme', 'default')

    def tearDown(self):
        pass

    def test_default_theme_active(self):
        """Test theme and is_active_theme for default theme
        """
        self.assertTrue(self.themesys.is_active_theme('default'))
        self.assertFalse(self.themesys.is_active_theme('themefull'))
        self.assertFalse(self.themesys.is_active_theme('themebase'))


def test_suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(ThemeSystemTestCase, 'test'))
    return test_suite

if __name__ == '__main__':
    unittest.main(suite=test_suite)

