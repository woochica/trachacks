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

from trac.core import Component, implements
from trac.test import EnvironmentStub

from themeengine.api import IThemeProvider, ThemeEngineSystem, ThemeBase

class FullTheme(Component):
    implements(IThemeProvider)

    # IThemeProvider methods
    def get_theme_names(self):
        yield 'full'
        yield 'quick'

    def get_theme_info(self, name):
        return dict(disable_trac_css=True)


class QuickTheme(ThemeBase):
    disable_trac_css = True


class ThemeSystemTestCase(unittest.TestCase):
    """Unit tests covering the theme system API
    """
    def setUp(self):
        self.env = env = EnvironmentStub(enable=['trac.*', 'themeengine.*'])
        self.themesys = ThemeEngineSystem(env)

    def tearDown(self):
        pass

    def test_default_theme_active(self):
        """Test theme and is_active_theme for default theme
        """
        env = self.env

        env.config.set('theme', 'theme', 'default')
        self.assertTrue(self.themesys.is_active_theme('default'))
        self.assertTrue(self.themesys.is_active_theme('default', 
                                                      self.themesys))
        self.assertFalse(self.themesys.is_active_theme('full'))
        self.assertFalse(self.themesys.is_active_theme('quick'))

        env.config.remove('theme', 'theme')
        self.assertTrue(self.themesys.is_active_theme('default'))
        self.assertFalse(self.themesys.is_active_theme('full'))
        self.assertFalse(self.themesys.is_active_theme('quick'))

    def test_theme_misconfiguration(self):
        """Fall back to default theme on misconfiguration
        """
        env = self.env

        env.config.set('theme', 'theme', 'wrong')
        self.assertTrue(self.themesys.is_active_theme('default'))
        self.assertTrue(self.themesys.is_active_theme('default', 
                                                      self.themesys))
        self.assertFalse(self.themesys.is_active_theme('full'))
        self.assertFalse(self.themesys.is_active_theme('quick'))
        self.assertFalse(QuickTheme(env).is_active_theme)

    def test_custom_theme_active(self):
        """Test theme and is_active_theme for custom theme
        """
        env = self.env

        env.config.set('theme', 'theme', 'full')
        self.assertFalse(self.themesys.is_active_theme('default'))
        self.assertTrue(self.themesys.is_active_theme('full'))
        self.assertTrue(self.themesys.is_active_theme('full',
                                                      FullTheme(env)))
        self.assertFalse(self.themesys.is_active_theme('quick'))
        self.assertFalse(QuickTheme(self.env).is_active_theme)

        env.config.set('theme', 'theme', 'quick')
        self.assertFalse(self.themesys.is_active_theme('default'))
        self.assertFalse(self.themesys.is_active_theme('full'))
        self.assertTrue(self.themesys.is_active_theme('quick'))
        self.assertTrue(self.themesys.is_active_theme('quick',
                                                      QuickTheme(env)))
        self.assertTrue(QuickTheme(env).is_active_theme)
        self.assertFalse(self.themesys.is_active_theme('quick',
                                                      FullTheme(env)))


def test_suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(ThemeSystemTestCase, 'test'))
    return test_suite

if __name__ == '__main__':
    unittest.main(suite=test_suite)

