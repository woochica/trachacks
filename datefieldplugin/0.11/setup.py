#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracDateField',
    version = '1.1.0',
    packages = ['datefield'],
    package_data = { 'datefield': ['templates/*.html', 'htdocs/css/*.css', 
        'htdocs/js/*.js', 'htdocs/css/images/*.png', 'htdocs/css/images/*.gif' ] },
    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Add custom date fields to Trac tickets.',
    license = 'BSD',
    keywords = 'trac plugin ticket',
    url = 'http://trac-hacks.org/wiki/DateFieldPlugin',
    classifiers = [
        'Framework :: Trac',
    ],    
    install_requires = ['Trac >= 0.11'],
    entry_points = {
        'trac.plugins': [
            'datefield.filter = datefield.filter',
        ]
    },
)
