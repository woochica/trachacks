#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracGamedevTheme',
    version = '2.0',
    packages = ['gamedevtheme'],
    package_data = { 'gamedevtheme': ['htdocs/*.*' ] },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
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
