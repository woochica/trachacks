#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'Toc',
    version = '1.0',
    packages = ['tractoc'],
    #package_data = { 'toc': ['templates/*.cs','htdocs/*' ] },

    author = "Alec Thomas",
    #author_email = "",
    description = "A macro to create tables of contents.",
    license = "BSD",
    keywords = "trac table of content macro",
    url = "http://trac-hacks.org/",

    entry_points = {
        'trac.plugins': [
            'tractoc.macro = tractoc.macro'
        ]
    },
)
