#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

PACKAGE = 'worklog'

setup(name=PACKAGE,
      description='Plugin to manage the which tickets users are currently working on',
      keywords='trac plugin ticket working',
      version='0.2',
      url='',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Colin Guthrie',
      author_email='trac@colin.guthr.ie',
      long_description="""
      I'll write this later!
      """,
      packages=[PACKAGE],
      package_data={PACKAGE : ['templates/*.cs', 'templates/*.html', 'htdocs/*.css', 'htdocs/*.png', 'htdocs/*.js']},
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)})


#### AUTHORS ####
## Primary Author:
## Colin Guthrie
## http://colin.guthr.ie/
## trac@colin.guthr.ie
## trac-hacks user: coling

