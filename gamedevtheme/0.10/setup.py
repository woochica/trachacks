#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracGamedevTheme',
    version = '1.0',
    packages = ['gamedevtheme'],
    package_data = { 'gamedevtheme': ['templates/*.cs', 'htdocs/*.jpg' ] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "A theme for Trac from the RPI game development club.",
    license = "BSD",
    keywords = "trac plugin theme",
    url = "http://trac-hacks.org/wiki/GamedevTheme",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracThemeEngine'],

    entry_points = {
        'trac.plugins': [
            'gamedevtheme.theme = gamedevtheme.theme',
        ]
    }
)
