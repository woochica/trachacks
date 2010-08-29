#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
  name = 'VisitCounter',
  version = '0.2',
  packages = ['visitcounter', 'visitcounter.db'],
  package_data = {'visitcounter' : ['templates/*.html', 'htdocs/*.png',
    'htdocs/css/*.css']},
  entry_points = {'trac.plugins': ['VisitCounter.core = visitcounter.core',
    'VisitCounter.init = visitcounter.init']},
  install_requires = ['Trac'],
  keywords = 'trac visitcounter',
  author = 'Radek Bartoň',
  author_email = 'blackhex@post.cz',
  url = 'http://trac-hacks.org/wiki/VisitCounterMacro',
  description = 'Visit counter macro for Trac',
  license = '''GPL'''
)
