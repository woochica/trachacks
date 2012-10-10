#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
  name = 'TracScreenshots',
  version = '0.4',
  packages = ['tracscreenshots', 'tracscreenshots.db'],
  package_data = {'tracscreenshots' : ['templates/*.cs', 'htdocs/css/*.css']},
  entry_points = {'trac.plugins': ['TracScreenshots.core = tracscreenshots.core',
    'TracScreenshots.init = tracscreenshots.init',
    'TracScreenshots.tags = tracscreenshots.tags',
    'TracScreenshots.wiki = tracscreenshots.wiki']},
  # If next line is not commented environment upgrade won't work on Trac 0.9.
  # If it is commented TracTags won't work.
  #install_requires = ['TracTags'],
  keywords = 'trac screenshots',
  author = 'Radek Bartoň',
  author_email = 'blackhex@post.cz',
  url = 'http://trac-hacks.org/wiki/ScreenshotsPlugin',
  description = 'Project screenshots plugin for Trac',
  license = '''GPL'''
)
