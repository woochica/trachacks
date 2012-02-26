#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracSpoilerMacro',
    version = '0.3',
    packages = ['spoiler'],
    package_data={ 'spoiler' : [ 'htdocs/css/*.css', 'htdocs/js/*.js' ] },
    author = "Benjamin Lau",
    description = "Macro to add spoiler button to a wiki page which allows for text to be hidden or shown.",
    license = "BSD",
    keywords = "trac plugin macro",
    url = "http://trac-hacks.org/wiki/SpoilerMacro",
    classifiers = [
        'Framework :: Trac',
    ],
    
    entry_points = {
        'trac.plugins': [
            'spoiler.macro = spoiler.macro',
        ],
    },
)
