#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracListOfWikiPagesMacro',
    version = '0.3',
    packages = ['traclistofwikipages'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    package_data = {
        'traclistofwikipages' : [ 'htdocs/*.css' ],
    },
    description = "Example Trac Macro.",
    url = 'http://www.trac-hacks.org/wiki/ExampleMacro',
    license = 'GPLv3',
    keywords = 'trac list wiki page macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['traclistofwikipages.macro = traclistofwikipages.macro']}
)
