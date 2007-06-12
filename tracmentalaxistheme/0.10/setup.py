#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracMentalaxisTheme',
    version = '1.0',
    packages = ['mentalaxistheme'],
    package_data = { 'mentalaxistheme': ['templates/*.cs', 'htdocs/*.png', 'htdocs/*.gif'] },

    author = "Jason Milkins",
    author_email = 'jason@mentalaxis.com',
    maintainer = 'Jason Milkins',
    maintainer_email = "jason@mentalaxis.com",
    description = "A theme for Trac by mentalaxis.com",
    license = "BSD",
    keywords = "trac plugin theme",
    url = "http://mentalaxis.com",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracThemeEngine'],

    entry_points = {
        'trac.plugins': [
            'mentalaxistheme.theme = mentalaxistheme.theme',
        ]
    }
)
