#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Alex Thomas
# Copyright (C) 2007-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2010-2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name = 'FootNoteMacro',
    version = '1.03',
    packages = ['footnotemacro'],
    package_data = { 'footnotemacro': ['htdocs/*.css',
                                       'htdocs/*.js'] },
    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryan.j.ollos@gmail.com',
    description = 'Add footnotes to a wiki page',
    license = '3-Clause BSD',
    keywords = 'trac plugin',
    url = 'http://trac-hacks.org/wiki/FootNoteMacroPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    install_requires = ['Trac'],
    entry_points = {
        'trac.plugins': [
            'footnotemacro.macro = footnotemacro.macro',
        ]
    },
)
