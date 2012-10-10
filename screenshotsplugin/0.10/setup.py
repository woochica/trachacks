#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
  name = 'TracScreenshots',
  version = '0.5',
  packages = ['tracscreenshots', 'tracscreenshots.db'],
  package_data = {'tracscreenshots' : ['templates/*.cs', 'htdocs/css/*.css',
    'htdocs/js/*.js']},
  entry_points = {'trac.plugins': ['TracScreenshots.api = tracscreenshots.api',
    'TracScreenshots.core = tracscreenshots.core',
    'TracScreenshots.init = tracscreenshots.init',
    'TracScreenshots.matrix_view = tracscreenshots.matrix_view',
    'TracScreenshots.wiki = tracscreenshots.wiki',
    'TracScreenshots.tags = tracscreenshots.tags [Tags]']},
  install_requires = [],
  extras_require = {'Tags' : ['TracTags']},
  keywords = 'trac screenshots',
  author = 'Radek Bartoň',
  author_email = 'blackhex@post.cz',
  url = 'http://trac-hacks.org/wiki/ScreenshotsPlugin',
  description = 'Project screenshots plugin for Trac',
  license = '''GPL'''
)
