#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracIncludeMacro',
    version = '2.0',
    packages = ['includemacro'],
    #package_data = { 'includemacro': ['templates/*.cs', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Include the contents of external URLs and other Trac objects in a wiki page.",
    license = "BSD",
    keywords = "trac plugin wiki include macro",
    url = "http://trac-hacks.org/wiki/IncludeMacro",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'includemacro.macros = includemacro.macros',
        ]
    }
)
