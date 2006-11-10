#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracDatamoverPlugin',
    version = '1.0',
    packages = ['datamover'],
    package_data={ 'datamover' : [ 'templates/*.cs' ] },
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Move data between Trac instances.",
    long_description = "Move/copy tickets and wiki pages from one Trac instance to another on the same server.",
    license = "BSD",
    keywords = "trac plugin data move copy",
    url = "http://trac-hacks.org/wiki/DatamoverPlugin",

    entry_points = {
        'trac.plugins': [
            'datamover.providers = datamover.providers',
            'datamover.web_ui = datamover.web_ui',
            'datamover.ticket = datamover.ticket',
            'datamover.wiki = datamover.wiki',
        ],
    },

    install_requires = [ 'TracWebAdmin' ],
    
    classifiers = [
        'Framework :: Trac',
    ],
)
