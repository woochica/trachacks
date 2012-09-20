#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os.path

from setuptools import setup

setup(
    name = 'TracIncludeMacro',
    version = '3.0.0',
    packages = ['includemacro'],

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryan.j.ollos@gmail.com',
    description = 'Include the contents of external URLs and other Trac objects in a wiki page.',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = '3-Clause BSD',
    keywords = 'trac 0.11 plugin wiki include macro',
    url = 'http://trac-hacks.org/wiki/IncludeMacro',
    classifiers = [
        'Framework :: Trac',
    ],
    install_requires = ['Trac'],
    entry_points = {
        'trac.plugins': [
            'includemacro.macros = includemacro.macros',
        ]
    }
)
