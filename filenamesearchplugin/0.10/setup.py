#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracFilenameSearch',
    version = '1.0',
    packages = ['filenamesearch'],
    #package_data = { 'filenamesearch': ['templates/*.cs', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Filename search for Trac.",
    long_description = "Search provider for Trac to query filenames in the repository.",
    license = "BSD",
    keywords = "trac plugin search filename",
    url = "http://trac-hacks.org/wiki/FilenameSearchPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    entry_points = {
        'trac.plugins': [
            'filenamesearch.web_ui = filenamesearch.web_ui'
        ]
    }
)
