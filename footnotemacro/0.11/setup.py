#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracFootNoteMacro',
    version = '1.0',
    packages = ['footnotemacro'],
    package_data = { 'footnotemacro': ['htdocs/*.css' ] },

    author = 'Noah Kantrowitz',
    author_email = 'coderanger@yahoo.com',
    description = '',
    license = 'BSD',
    keywords = 'trac plugin',
    url = 'http://trac-hacks.org/wiki/FootNoteMacroPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'footnotemacro.macro = footnotemacro.macro',
        ]
    },
)
