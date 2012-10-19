#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'Wikinfo',
    version = '0.1',
    packages = ['wikinfo'],
    package_data = {  },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Provides a few useful macros to get data about wiki pages",
    license = "BSD",
    keywords = "trac wiki info macro",
    url = "http://trac-hacks.org/",

    entry_points = {
        'trac.plugins': [
            'wikinfo.wikinfo = wikinfo.wikinfo'
        ]
    }
)

