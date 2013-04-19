#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Jeff Hammel <jhammel@openplans.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup, find_packages

version = '0.2.1'

setup(name='TracSQLHelper',
      version=version,
      description="SQL Helper functions for Trac",
      long_description="""SQL Helper functions for Trac
                       """,
      classifiers=[],
      keywords='SQL Trac',
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      license='BSD 3-Clause',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=['Trac'],
      entry_points="""
      """,
      )
