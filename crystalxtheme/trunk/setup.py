#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracCrystalXTheme',
    version = '1.0',
    packages = ['crystalxtheme'],
    package_data = { 'crystalxtheme': ['templates/*.html', 'htdocs/*.png', 'htdocs/*.css', 'htdocs/img/*.gif', 'htdocs/img/*.jpg' ] },

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'A theme for Trac based on http://www.oswd.org/design/information/id/3465.',
    license = 'BSD',
    keywords = 'trac plugin theme',
    url = 'http://trac-hacks.org/wiki/CrystalXTheme',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac', 'TracThemeEngine>=2.0'],

    entry_points = {
        'trac.plugins': [
            'crystalxtheme.theme = crystalxtheme.theme',
        ]
    },
)
