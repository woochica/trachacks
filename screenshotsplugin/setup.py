#!/usr/bin/env python
# -*- coding: utf8 -*-

from setuptools import setup

setup(
  name = 'TracScreenshotsPlugin',
  version = '0.3',
  packages = ['tracscreenshots', 'tracscreenshots.db'],
  package_data = {'tracscreenshots' : ['templates/*.cs', 'htdocs/css/*.css']},
  entry_points = {'trac.plugins': ['TracScreenshotsPlugin.core = tracscreenshots.core',
    'TracScreenshotsPlugin.init = tracscreenshots.init',
    'TracScreenshotsPlugin.tags = tracscreenshots.tags',
    'TracScreenshotsPlugin.wiki = tracscreenshots.wiki']},
  keywords = 'trac screenshots',
  author = 'Radek Bartoň',
  author_email = 'trac-hacks@swapoff.org',
  url = 'http://trac-hacks.swapoff.org/wiki/ScreenshotsPlugin',
  description = 'Project screenshots plugin for Trac',
  license = '''GPL'''
)
