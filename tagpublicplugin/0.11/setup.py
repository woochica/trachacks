#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TagPublic',
    version = '0.0.1',
    packages = ['tagpublic'],

    author = "Joachim Steiger",
    author_email = "trac@hyte.de",
    description = "make tagged public things available public",
    long_description = "Allow access to wikipages and Blogposts when tagged public.",
    license = "BSD",
    keywords = "trac plugin wiki blog permissions security",
    url = "http://trac-hacks.org/wiki/TagPublicPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    entry_points = {
        'trac.plugins': [
            'tagpublic = tagpublic',
        ]
    }    
)
