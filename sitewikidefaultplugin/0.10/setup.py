#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracSiteWikiDefault',
    version = '1.0',
    packages = ['sitewikidefault'],

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Modify pages in the Trac wiki at initialization",
    #long_description = "Provides a web interface to removing whole tickets and ticket changes in Trac.",
    license = "BSD",
    keywords = "trac plugin wiki default",
    url = "http://trac-hacks.org/wiki/SiteWikiDefaultPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    #install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'sitewikidefault.api = sitewikidefault.api'
        ]
    }
)
