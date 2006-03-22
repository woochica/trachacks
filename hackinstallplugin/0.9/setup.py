#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'HackInstall',
    version = '0.5',
    packages = ['hackinstall'],
    package_data = { 'hackinstall': ['templates/*.cs','htdocs/*' ] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "A plugin manager for Trac-Hacks plugins.",
    license = "BSD",
    keywords = "trac plugin manager hacks",
    url = "http://trac-hacks.org/",

    entry_points = {
        'trac.plugins': [
            'hackinstall.web_ui = hackinstall.web_ui'
        ]
    }
)
