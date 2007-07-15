#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracOhlohBadge',
    version = '1.0',
    packages = ['ohlohbadge'],
    #package_data = { 'ohlohbadge': ['templates/*.cs', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = 'Noah Kantrowitz',
    author_email = 'noah+pypi@coderanger.net',
    description = 'A Trac wiki macro to display Ohlo project badges.',
    license = 'BSD',
    keywords = 'trac plugin macro ohloh badge',
    url = 'http://trac-hacks.org/wiki/OhlohBadgeMacro',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = [],

    entry_points = {
        'trac.plugins': [
            'ohlohbadge.macro = ohlohbadge.macro',
        ]
    },
)
