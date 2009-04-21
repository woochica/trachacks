#!/usr/bin/env python
# -*- coding: utf8 -*-

from setuptools import setup

setup(
  name = 'TracDownloads',
  version = '0.2',
  packages = ['tracdownloads', 'tracdownloads.db'],
  package_data = {'tracdownloads' : ['templates/*.html', 'htdocs/css/*.css']},
  entry_points = {'trac.plugins': ['TracDownloads.api = tracdownloads.api',
    'TracDownloads.core = tracdownloads.core',
    'TracDownloads.init = tracdownloads.init',
    'TracDownloads.admin = tracdownloads.admin',
    'TracDownloads.wiki = tracdownloads.wiki',
    'TracDownloads.timeline = tracdownloads.timeline',
    'TracDownloads.tags = tracdownloads.tags [Tags]']},
  extras_require = {'Tags' : ['TracTags']},
  keywords = 'trac downloads',
  author = 'Radek Bartoň',
  author_email = 'blackhex@post.cz',
  url = 'http://trac-hacks.org/wiki/DownloadsPlugin',
  description = 'Project release downloads plugin for Trac',
  license = '''GPL'''
)
