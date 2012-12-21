#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martin Aspeli <optilude@gmail.com>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name = 'WikiTableMacro',
    author = 'Martin Aspeli',
    author_email = 'optilude@gmail.com',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryan.j.ollos@gmail.com',
    description = 'Trac plugin for drawing a table from a SQL query in a wiki page',
    url = 'http://trac-hacks.org/wiki/WikiTableMacro', 
    version = '0.2',
    license='3-Clause BSD',
    packages=['wikitable'],
    package_data={'wikitable': ['htdocs/css/*.css',]},
    entry_points = {
        'trac.plugins': [
            'wikitable.table = wikitable.table',
            'wikitable.scalar = wikitable.scalar'
        ]
    },
)
