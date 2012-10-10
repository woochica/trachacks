#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2010 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name = 'TracThemeEngine',
    version = '1.0',
    packages = ['themeengine'],
    package_data = { 'themeengine': [ 'templates/*.cs', 'templates/header/*.cs', 'templates/footer/*.cs', 
                                      'htdocs/*.*', 'htdocs/img/*.*' ] },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Provide a modular interface to styling Trac.",
    license = "3-Clause BSD",
    keywords = "trac plugin theme style",
    url = "http://trac-hacks.org/wiki/ThemeEnginePlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'themeengine.filter = themeengine.filter',
            'themeengine.admin = themeengine.admin',
        ]
    }
)
