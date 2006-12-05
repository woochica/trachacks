#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracDelegatedWiki',
    version = '1.0',
    packages = ['delegatedwiki'],
    #package_data={ 'delegatedwiki' : [ 'templates/*.cs' ] },
    author = "Bryan Tsai",
    author_email = "bryan@bryantsai.com",
    description = "Make the Trac wiki delegated (to other site).",
    long_description = "",
    license = "BSD",
    keywords = "trac plugin wiki delegated wiki",
    url = "http://trac-hacks.org/wiki/TracDelegatedWiki",
    classifiers = [
        'Framework :: Trac',
    ],

    entry_points = {
        'trac.plugins': [
            'delegatedwiki.filter = delegatedwiki.filter',
        ],
    },
)

