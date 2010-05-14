#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracHierWiki',
    version = '1.0',
    packages = ['hierwiki', 'hierwiki/macros' ],
    #package_data={ 'hierwiki' : [ ] },
    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Hierarchical wiki utilities for Trac.",
    long_description = "Various things related to using the Trac wiki in hierarchical way.",
    license = "BSD",
    keywords = "trac plugin macros wiki hierarchy",
    url = "http://trac-hacks.org/wiki/HierWikiPlugin",
    classifiers = [
        'Framework :: Trac',
    ],

    entry_points = {
        'trac.plugins': [
            'hierwiki.filter = hierwiki.filter',
            'hierwiki.formatter = hierwiki.formatter',
            'hierwiki.macros = hierwiki.macros',
        ],
    },

    install_requires = [ ],
)
