#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracDropbears',
    version = '2.0',
    packages = ['dropbears'],
    package_data = { 'dropbears': ['templates/*.html', 'templates/*.js', 'htdocs/*.gif', 'htdocs/*.css' ] },

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Aaaaaaaaah! The Dropbears cometh!',
    license = 'BSD',
    keywords = 'trac plugin dropbears',
    url = 'http://trac-hacks.org/wiki/DropbearsPlugin',
    classifiers = [
        'Framework :: Trac',
    ],

    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'dropbears.web_ui = dropbears.web_ui',
        ]
    },
)
