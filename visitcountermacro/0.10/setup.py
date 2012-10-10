#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
  name = 'VisitCounter',
  version = '0.1',
  packages = ['visitcounter', 'visitcounter.db'],
  package_data = {'visitcounter' : ['templates/*.cs', 'htdocs/*.png',
    'htdocs/css/*.css']},
  entry_points = {'trac.plugins': ['VisitCounter.core = visitcounter.core',
    'VisitCounter.init = visitcounter.init']},
  keywords = 'trac visitcounter',
  author = 'Radek Bartoň',
  author_email = 'blackhex@post.cz',
  url = 'http://trac-hacks.org/wiki/VisitCounterMacro',
  description = 'Visit counter macro for Trac',
  license = 'GPL'
)
