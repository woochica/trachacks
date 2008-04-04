#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracPrivateTickets',
    version = '2.0',
    packages = ['privatetickets'],

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

    entry_points = {
        'trac.plugins': [
            'privatetickets.policy = privatetickets.policy',
        ],
    },
)
