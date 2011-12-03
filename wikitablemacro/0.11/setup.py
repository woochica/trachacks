#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'WikiTableMacro',
    author = 'Martin Aspeli',
    author_email = 'optilude@gmail.com',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryano@physiosonics.com',
    description = 'Trac plugin for drawing a table from a SQL query in a wiki page',
    url = 'http://trac-hacks.org/wiki/WikiTableMacro', 
    version = '0.1',
    license='BSD',
    packages=['wikitable'],
    package_data={'wikitable': ['htdocs/css/*.css',]},
    entry_points = {
        'trac.plugins': [
            'wikitable = wikitable'
        ]
    },
)
