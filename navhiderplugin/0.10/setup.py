#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracNavHider',
    version = '1.0',
    packages = ['navhider'],
    #package_data = { 'navhider': ['templates/*.cs', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Remove items from the Trac navigation bars.",
    license = "BSD",
    keywords = "trac plugin navigation menu remove hide",
    url = "http://trac-hacks.org/wiki/NavHiderPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    #install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'navhider.filter = navhider.filter',
        ]
    }
)
