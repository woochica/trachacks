#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracMultiSelectField',
    version = '1.0.0',
    packages = ['multiselectfield'],
    package_data = { 'multiselectfield': ['htdocs/*.css', 
        'htdocs/*.js', 'htdocs/*.png' ] },
    author = 'Olli Kallioinen',
    author_email = 'olli.kallioinen@iki.fi',
    description = 'A plugin providing a multiselection custom ticket field.',
    license = 'BSD',
    keywords = 'trac plugin multiselection',
    classifiers = [
        'Framework :: Trac',
    ],
    install_requires = ['Trac >= 1.0'],
    entry_points = {
        'trac.plugins': [
            'multiselectfield.filter = multiselectfield.filter',
        ]
    },
)
