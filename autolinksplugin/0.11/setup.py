#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TracAutoLinks',
    version = '1.0',
    packages = ['autolinks'],
    author = "Chris Lajoie",
    author_email = "ctlajoie@gmail.com",
    description = "Automatically creates links to wiki pages for Proper Cased Words and acronyms if the page exists",
    long_description = "",
    license = "BSD",
    keywords = "trac plugin wiki proper case acronym links",
    url = "http://trac-hacks.org/wiki/AutoLinksPlugin",
    classifiers = [
        'Framework :: Trac',
    ],

    entry_points = {
        'trac.plugins': [
            'TracAutoLinks = autolinks.autolinks',
        ],
    },
)
