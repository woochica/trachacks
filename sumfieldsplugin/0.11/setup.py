#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracSumFields',
    version = '1.0.1',
    packages = ['sumfields'],
    package_data = { 'sumfields': ['templates/*.html'] },

    author = 'Rob Guttman',
    author_email = 'guttman@alum.mit.edu',
    description = 'Sum fields in Trac custom queries.',
    license = 'BSD',
    keywords = 'trac plugin sum',
    url = 'http://trac-hacks.org/wiki/SumFieldsPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = [],

    entry_points = {
        'trac.plugins': [
            'sumfields.web_ui = sumfields.web_ui',
        ]
    },
)
