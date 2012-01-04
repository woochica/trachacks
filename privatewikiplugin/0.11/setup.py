#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'PrivateWikis',
    version = '1.0.0',
    packages = ['privatewiki'],

    author = "Eric Hodges",
    author_email = "eric.hodges@gmail.com",
    description = "Add private wiki ability.",
    maintainer = "Nathan Lewis",
    maintainer_email = "natewlew@gmail.com",
    long_description = "Allow admins to restrict access to wikis.",
    license = "BSD",
    keywords = "trac plugin wiki permissions security",
    url = "http://trac-hacks.org/wiki/PrivateWikiPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    entry_points = {
        'trac.plugins': [
            'privatewiki = privatewiki',
        ]
    }    
)
