#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup

setup(
    name = 'TracOpenIDDelegate',
    version = '1.0',
    packages = ['openiddelegate'],

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Add OpenID delegation links to a Trac site.',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = 'BSD',
    keywords = 'trac plugin',
    url = 'http://trac-hacks.org/wiki/OpenIDDelegatePlugin',
    classifiers = [
        'Framework :: Trac',
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'openiddelegate.filter = openiddelegate.filter',
        ]
    },
)
