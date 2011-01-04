#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracHideChanges',
    version = '1.0.0',
    packages = ['hidechanges'],
    package_data = { 'hidechanges': ['templates/*.html'] },

    author = 'Rob Guttman',
    author_email = 'guttman@alum.mit.edu',
    description = 'Hide ticket changes based on configurable rules.',
    license = 'GPL',
    keywords = 'trac plugin hide changes',
    url = 'http://trac-hacks.org/wiki/HideChangesPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = [],

    entry_points = {
        'trac.plugins': [
            'hidechanges.web_ui = hidechanges.web_ui',
        ]
    },
)
