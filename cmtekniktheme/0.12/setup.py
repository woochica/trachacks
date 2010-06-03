#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'CMTeknikTheme',
    version = '1.0',
    packages = [ 'cmtekniktheme' ],
    package_data = { 'cmtekniktheme': [ 'htdocs/*.css', 'htdocs/*.png', 'htdocs/*.gif', 'templates/*.html' ] },
    author = 'Jonatan Magnusson',
    author_email = 'jonatan@cmteknik.se',
    description = 'A theme for Trac based on http://www.cmteknik.se',
    license = 'BSD',
    keywords = 'trac plugin theme',
    url = 'http://trac-hacks.org/wiki/CMTeknikTheme',
    classifiers = [
        'Framework :: Trac',
    ],
    install_requires = [ 'Trac', 'TracThemeEngine>=2.0' ],

    entry_points = {
        'trac.plugins': [
            'cmtekniktheme.theme = cmtekniktheme.theme',
        ]
    },
)

