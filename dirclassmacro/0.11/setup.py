#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'DirClassMacro',
    version = '0.11-2',
    packages = ['dirclass'],
    package_data = { 'dirclass': ['htdocs/css/*.css' ] },

    author = "Itamar Ostricher",
    author_email = "itamarost@gmail.com",
    description = "DirClass Macro for Trac",
    long_description = """The DirClass macro provides macros to assist in controlling the alignment of wiki content.""",
    license = "BSD",
    keywords = "trac plugin macro dir rtl ltr",
    url = "http://trac-hacks.org/wiki/DirClassMacro",

    entry_points = {
        'trac.plugins': [
            'dirclass.macro = dirclass.macro'
        ]
    },
)
