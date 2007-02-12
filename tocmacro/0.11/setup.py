#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracTocMacro',
    version = '11.0.0.2',
    packages = ['tractoc'],
    #package_data = { 'toc': ['templates/*.cs','htdocs/*' ] },

    author = "Alec Thomas",
    #author_email = "",
    maintainer = "Christian Boos",
    maintainer_email = "cboosr@neuf.fr",
    description = "A macro to create tables of contents.",
    long_description = """A macro to create a table of contents for either a \
                          single page, or a collection of pages.""",
    license = "BSD",
    keywords = "trac plugin table of content macro",
    url = "http://trac-hacks.org/wiki/TocMacro",

    entry_points = {
        'trac.plugins': [
            'tractoc.macro = tractoc.macro'
        ]
    },
)
