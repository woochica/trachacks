#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracHideVals',
    version = '1.1',
    packages = ['hidevals'],
    package_data = { 'hidevals': ['templates/*.cs', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Hide ticket option values from certain users.',
    license = 'BSD',
    keywords = 'trac plugin',
    url = 'http://trac-hacks.org/wiki/HideValsPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'hidevals.filter = hidevals.filter',
            'hidevals.api = hidevals.api',
            'hidevals.admin = hidevals.admin',
        ]
    },
)
