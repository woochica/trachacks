#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracCombineWiki',
    version = '1.0',
    packages = ['combinewiki'],
    package_data={ 'combinewiki' : [ 'templates/*.cs' ] },
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Export a subset of the wiki as a single file..",
    license = "BSD",
    keywords = "trac plugin combine wiki pdf",
    url = "http://trac-hacks.org/wiki/CombineWikiPlugin",

    entry_points = {
        'trac.plugins': [
            'combinewiki.web_ui = combinewiki.web_ui',
        ],
    },

    install_requires = [ 'TracWebAdmin' ],
)
