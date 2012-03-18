#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracPrivateTickets',
    version = '1.1.1',
    packages = ['privatetickets'],
    #package_data = { 'privatetickets': ['templates/*.cs', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Modified ticket security for Trac.",
    long_description = "Allow users to only see tickets are involved with.",
    license = "BSD",
    keywords = "trac plugin ticket permissions security",
    url = "http://trac-hacks.org/wiki/PrivateTickets",
    classifiers = [
        'Framework :: Trac',
    ],
    
    #install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'privatetickets.api = privatetickets.api',
            'privatetickets.view = privatetickets.view',
            'privatetickets.query = privatetickets.query',
            'privatetickets.report = privatetickets.report',
            'privatetickets.search = privatetickets.search',
        ]
    }
)
