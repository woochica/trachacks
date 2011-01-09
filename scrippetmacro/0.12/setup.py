#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracScrippetsMacro',
    version = '0.1',
    packages = ['scrippets'],
    package_data={ 'scrippets' : [ 'htdocs/css/*.css' ] },
    author = "Benjamin Lau",
    description = "Macro to add scrippets to a wiki page.",
    license = "BSD",
    keywords = "trac plugin macro comments",
    url = "http://trac-hacks.org/wiki/ScrippetsMacro",
    classifiers = [
        'Framework :: Trac',
    ],
    
    entry_points = {
        'trac.plugins': [
            'scrippets.macro = scrippets.macro',
        ],
    },
)
