#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Brian Lynch <blynch1@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

PACKAGE = 'TracFileList'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      author='Brian Lynch',
      author_email='blynch1@gmail.com',
      license='3-Clause BSD',
      packages=['filelist'],
      package_dir={'filelist': 'filelist'},
      package_data={'filelist':['htdocs/js/*.js']},
      entry_points={'trac.plugins': '%s = filelist' % PACKAGE},
)

