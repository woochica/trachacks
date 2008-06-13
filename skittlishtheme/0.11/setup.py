#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
  name         = 'TracSkittlishTheme',
  version      = '2.0',
  packages     = ['skittlishtheme'],
  package_data = { 'skittlishtheme': ['templates/*.html', 'htdocs/*.css', 'htdocs/images/*.gif' ] },

  author           = 'Danial Pearce',
  author_email     = 'trac-themes@tigris.id.au',
  description      = 'A port of the mephisto theme, Skittlish, created by evil.che.lu.',
  license          = 'BSD',
  keywords         = 'skittlish trac plugin theme',
  url              = 'http://trac-hacks.org/wiki/SkittlishTheme',
  classifiers      = [
    'Framework :: Trac'
  ],

  install_requires = ['Trac', 'TracThemeEngine>=2.0'],

  entry_points = {
    'trac.plugins': [
      'skittlishtheme.theme = skittlishtheme.theme',
    ]
  },
)
