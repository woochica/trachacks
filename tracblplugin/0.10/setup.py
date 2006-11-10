#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracBL',
    version = '1.0',
    packages = ['tracbl'],
    package_data = { 'tracbl': ['templates/*.cs', 'htdocs/js/*.js', 'htdocs/css/*.css' ] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Domain blacklisting for Trac.",
    license = "BSD",
    keywords = "trac plugin ticket delete",
    url = "http://trac-hacks.org/wiki/TracBLPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'tracbl.api = tracbl.api'
        ]
    }
)
