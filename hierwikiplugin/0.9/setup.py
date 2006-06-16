#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracHierWiki',
    version = '0.1',
    packages = ['hierwiki'],
    package_data={ 'hierwiki' : [ ] },
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Hierarchical wiki macros.",
    long_description = "Various things related to using the wiki in hierarchical way.",
    license = "BSD",
    keywords = "trac plugin macros wiki hierarchy",
    url = "http://trac-hacks.org/wiki/HierWikiPlugin",

    entry_points = {
        'trac.plugins': [
            'hierwiki.macros = hierwiki.macros',
        ],
    },

    install_requires = [ ],
)
