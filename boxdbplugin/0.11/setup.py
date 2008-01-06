#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracBoxDB',
    version = '1.0',
    packages = ['boxdb'],
    package_data = { 'boxdb': ['templates/*.html', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = 'Noah Kantrowitz',
    author_email = 'coderanger@yahoo.com',
    description = '',
    license = 'BSD',
    keywords = 'trac plugin',
    url = 'http://trac-hacks.org/wiki/BoxDBPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'boxdb.web_ui = boxdb.web_ui',
            'boxdb.api = boxdb.api',
            'boxdb.properties = boxdb.properties',
        ]
    },
)
