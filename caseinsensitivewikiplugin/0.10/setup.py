#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracCaseInsensitiveWiki',
    version = '1.0',
    packages = ['caseinsensitivewiki'],
    #package_data={ 'caseinsensitivewiki' : [ 'templates/*.cs' ] },
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Make the Trac wiki case-insensitive.",
    long_description = "",
    license = "BSD",
    keywords = "trac plugin wiki case insensitive",
    url = "http://trac-hacks.org/wiki/CaseInsensitiveWiki",
    classifiers = [
        'Framework :: Trac',
    ],

    entry_points = {
        'trac.plugins': [
            'caseinsensitivewiki.filter = caseinsensitivewiki.filter',
        ],
    },

    #install_requires = [ 'TracWebAdmin' ],
    
)
