#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracCtxtnavAdd',
    version = '2.0',
    packages = ['ctxtnavadd'],
    package_data={ 'ctxtnavadd' : [ 'templates/*.js' , 'htdocs/js/*.js' ] },
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Allow adding to the ctxtnav bar of other plugins.",
    long_description = "Exposes an extension point interface for manipulating the ctxtnav bar (the little bar below the main navigation bar) of other plugins",
    license = "BSD",
    keywords = "trac plugin ctxtnav",
    url = "http://trac-hacks.org/wiki/CtxtnavAddPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    entry_points = {
        'trac.plugins': [
            'ctxtnavadd.web_ui = ctxtnavadd.web_ui',
        ],
    },
)
