#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracCombineWiki',
    version = '1.2',
    packages = ['combinewiki'],
    package_data={ 'combinewiki' : [ 'templates/*.cs' ] },
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Export a subset of a Trac wiki as a single file.",
    long_description = "Export multiple wiki pages to a single file. Automatically generates a title page and table of contents.",
    license = "BSD",
    keywords = "trac plugin combine wiki pdf",
    url = "http://trac-hacks.org/wiki/CombineWikiPlugin",
    classifiers = [
        'Framework :: Trac',
    ],

    entry_points = {
        'trac.plugins': [
            'combinewiki.formats = combinewiki.formats',
            'combinewiki.web_ui = combinewiki.web_ui',
        ],
    },

    install_requires = [ 'TracWebAdmin' ],
    
)
