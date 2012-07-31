#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Alec Thomas
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup, find_packages

setup(name='TracAutoWikify',
      version='0.2',
      description='Wikify all wiki page names, including non-CamelCase ones.',
      
      author='Alec Thomas',
      maintainer='Ryan J Ollos',
      maintainer_email='ryan.j.ollos@gmail.com',      
      url='http://trac-hacks.org/wiki/AutoWikifyPlugin',
      license='3-Clause BSD',
      
      packages=find_packages(exclude=['*.tests']),
      test_suite = 'tracautowikify.tests',
      tests_require = [],
      entry_points = {
          'trac.plugins': [
              'tracautowikify = tracautowikify.autowikify'
          ]
      }
)
