#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'FootNoteMacro',
    version = '1.03',
    packages = ['footnotemacro'],
    package_data = { 'footnotemacro': ['htdocs/*.css',
                                       'htdocs/*.js'] },
    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    maintainer = 'Ryan Ollos',
    maintainer_email = 'ryano@physiosonics.com',
    description = 'Add footnotes to a wiki page',
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
