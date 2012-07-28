#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(name='TracAutoWikify',
      version='0.2',
      packages=['tracautowikify'],
      author='Alec Thomas',
      description='Automatically create links for all known Wiki pages, even those that are not in CamelCase.',
      url='http://trac-hacks.org/wiki/AutoWikifyPlugin',
      license='BSD',
      entry_points = {'trac.plugins': ['tracautowikify = tracautowikify.autowikify']})
