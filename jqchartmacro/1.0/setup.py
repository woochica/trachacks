#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Pablo Gra\~na <pablo.grana@55social.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup (
    name = 'JQChart',
    version = 1.0,
    author = 'pablo.grana',
    author_email = 'pablo.pg@gmail.com',
    license = 'BSD',    
    url = 'http://trac-hacks.org/wiki/TBD',
    description = 'Provides jqplot based charts.',
    packages = find_packages(exclude=['*.tests']),
    package_data = { 'jqplotchart': ['htdocs/*.png','htdocs/*.js',
        'htdocs/*.css', 'htdocs/jqplot/*.js', 'htdocs/jqplot/plugins/*.js',
        'htdocs/jqplot/*.css'] },
    entry_points = {'trac.plugins': ['JQChart = jqplotchart.macro']},
    keywords = 'trac macro',
)

