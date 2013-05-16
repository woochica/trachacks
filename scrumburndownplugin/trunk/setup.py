#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Sam Bloomquist <spooninator@hotmail.com>
# Copyright (C) 2006-2008 Daan van Etten <daan@stuq.nl>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup, find_packages

PACKAGE = 'TracBurndown'
VERSION = '2.0.0'

setup(name=PACKAGE,
      description='Plugin to provide a dynamic burndown chart in Trac.',
      keywords='trac plugin scrum burndown',
      url='http://trac-hacks.org/wiki/ScrumBurndownPlugin',
      author="Daan van Etten, Sam Bloomquist and others",
      author_email="daan@stuq.nl",
      version=VERSION,
      license="Apache License, 2.0",
      packages=find_packages(exclude=['ez_setup']),
      package_data={
          'burndown': ['htdocs/js/*.js', 'htdocs/css/*.css',
                       'htdocs/images/*', 'templates/*.html']
      },
      entry_points={'trac.plugins': '%s = burndown' % PACKAGE},
      tests_require=['nose'],
      test_suite='nose.collector'
      )
