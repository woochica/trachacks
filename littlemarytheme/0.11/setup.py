#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'LittleMary',
    version = '1.0',
    packages = [ 'littlemarytheme' ],
    package_data = { 'littlemarytheme': [ 'htdocs/*.css', 'htdocs/*.jpg','htdocs/*.png', 'htdocs/*.gif', 'templates/*.html' ] },
    author = 'Carlos Bonadeo',
    author_email = 'carlosbonadeo@gmail.com',
    description = 'A theme for Trac',
    license = 'BSD',
    keywords = 'trac plugin theme',
    url = 'http://trac-hacks.org/wiki/LittleMaryTheme',
    classifiers = [
        'Framework :: Trac',
    ],
    install_requires = [ 'Trac', 'TracThemeEngine>=2.0' ],

    entry_points = {
        'trac.plugins': [
            'littlemarytheme.theme = littlemarytheme.theme',
        ]
    },
)

