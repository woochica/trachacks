#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracSelfDelete',
    version = '1.0',
    packages = ['selfdelete'],
    #package_data = { 'selfdelete': ['templates/*.cs', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Remove Trac wiki pages and attachments that you created.",
    long_description = "Allows users to delete wiki pages and attachments that they created..",
    license = "BSD",
    keywords = "trac plugin wiki attachment delete",
    url = "http://trac-hacks.org/wiki/SelfDeletePlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    #install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'selfdelete.filter = selfdelete.filter',
        ]
    }
)
