#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TracFlexJs',
    version = '0.1',
    zip_safe = True,
    packages = ['flexjs'],
    
    author = "Clay Loveless",
    author_email = "clay@killersoft.com",
    description = "Provides flexible JavaScript awareness for Trac.",
    license = "New BSD",
    keywords = "trac plugin system javascript js",
    url = "http://trac-hacks.org/wiki/FlexJsPlugin",
    
    entry_points = {
        'trac.plugins': [
            'flexjs.flexjs = flexjs.flexjs',
        ]
    },
    
)