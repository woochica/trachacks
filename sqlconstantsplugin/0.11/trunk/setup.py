#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'sqlconstants',
    author = 'Martin Aspeli',
    author_email = 'optilude@gmail.com',
    description = 'Trac plugin for managing a set of constants in the database',
    version = '0.1',
    license='BSD',
    packages=['sqlconstants'],
    package_data={'sqlconstants': ['templates/*.html', 
                                   'htdocs/css/*.css',]},
    entry_points = {
        'trac.plugins': [
            'sqlconstants = sqlconstants'
        ]
    },
    install_requires = [
    ],
)
