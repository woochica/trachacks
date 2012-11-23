#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2007 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(name='TracHacks',
      version='0.1',
      packages=['trachacks'],
      license='3-Clause BSD',
      entry_points={'trac.plugins': 'TracHacks = trachacks'},
      #install_requires=['TracXMLRPC', 'TracAccountManager'],
      )
