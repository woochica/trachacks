#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracIntraBlogTheme',
    version = '1.0',
    packages = ['intrablogtheme'],
    package_data = { 'intrablogtheme': ['templates/*.cs', 'htdocs/images/*.*', 'htdocs/*.*' ] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "A theme for Trac based on the Intra Blog theme from templateworld.com",
    license = "BSD",
    keywords = "trac plugin theme",
    url = "http://trac-hacks.org/wiki/IntraBlogTheme",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracThemeEngine'],

    entry_points = {
        'trac.plugins': [
            'intrablogtheme.theme = intrablogtheme.theme',
        ]
    }
)
