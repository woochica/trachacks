#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'LightGreenTheme',
    version = '0.1',
    packages = ['lightgreentheme'],
    package_data = { 'lightgreentheme': ['htdocs/*.css', 'htdocs/*.png', 'htdocs/*.gif'] },

    author = "Radu Gasler",
    author_email = 'miezuit@gmail.com',
    description = "A theme for Trac based on http://projects.autonomy.net.au/hotwire/",
    url = "http://trac-hacks.org/wiki/LightGreenTheme",
    keywords = "trac plugin theme",

    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracThemeEngine'],

    entry_points = {
        'trac.plugins': [
            'lightgreentheme.theme = lightgreentheme.theme',
        ]
    }
)
