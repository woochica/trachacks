#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'TracGoogleMapMacro',
    version = '0.5',
    description = 'Provides Macro for Trac Wikis to allow users to add Google Maps.',
    license = 'GPLv3',
    url = 'http://trac-hacks.org/wiki/GoogleMapMacro',
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    packages = find_packages(exclude=['*.tests*','tools/*']),
    package_data = {
        'googlemapmacro' : [ 'htdocs/*.js' ],
    },
    entry_points = {
        'trac.plugins': [
            'googlemapmacro = googlemapmacro',
        ],
    }
)
