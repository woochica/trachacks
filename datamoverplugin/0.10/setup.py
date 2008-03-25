#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracDatamoverPlugin',
    version = '1.2',
    packages = ['datamover'],
    package_data={ 'datamover' : [ 'templates/*.cs' ] },
    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
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
            'datamover.component = datamover.component',
            'datamover.enum = datamover.enum',
            'datamover.milestone = datamover.milestone',
            'datamover.attachment = datamover.attachment',
            'datamover.version = datamover.version',
            'datamover.permission = datamover.permission',
        ],
    },

    install_requires = [ 'TracWebAdmin' ],
    
    classifiers = [
        'Framework :: Trac',
    ],
)
