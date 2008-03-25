#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracCacheSystem',
    version = '1.0',
    packages = ['cachesystem'],
    #package_data = { 'cachesystem': ['templates/*.cs', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Modular caching framework for Trac, currently using memcached as a backend.",
    license = "BSD",
    keywords = "trac plugin cache",
    url = "http://trac-hacks.org/wiki/CacheSystemPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    #install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'cachesystem.filter = cachesystem.filter',
        ]
    }
)
