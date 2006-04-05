#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'EasterMacro',
    version = '0.1',
    packages = ['easter'],
    package_data = { 'easter': ['htdocs/img/*.gif' ] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "A macro to tell you when Easter is.",
    license = "BSD",
    keywords = "trac macro easter",
    url = "http://trac-hacks.org/",

    entry_points = {
        'trac.plugins': [
            'easter.macro = easter.macro'
        ]
    }
)
