#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracThemeEngine',
    version = '1.0',
    packages = ['themeengine'],
    package_data = { 'themeengine': [ 'templates/*.cs', 'templates/header/*.cs', 'templates/footer/*.cs', 
                                      'htdocs/*.*', 'htdocs/img/*.*' ] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Provide a modular interface to styling Trac.",
    license = "BSD",
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
