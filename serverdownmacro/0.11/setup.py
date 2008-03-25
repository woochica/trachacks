#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracServerDownMacro',
    version = '1.0',
    packages = ['serverdownmacro'],
    package_data = { 'serverdownmacro': [] },

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = '',
    license = 'BSD',
    keywords = 'trac plugin',
    url = 'http://trac-hacks.org/wiki/ServerDownMacroPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'serverdownmacro.macro = serverdownmacro.macro',
        ]
    },
)
