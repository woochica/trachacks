#!/usr/bin/env python

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = ur"$Rev$"[6:-2]
__date__     = ur"$Date$"[7:-2]

setup(
    name = 'TracListOfWikiPagesMacro',
    version = '0.4',
    packages = ['traclistofwikipages'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    package_data = {
        'traclistofwikipages' : [ 'htdocs/*.css' ],
    },
    description = "ListOfWikiPagesMacro for Trac v0.12",
    url = 'http://www.trac-hacks.org/wiki/ListOfWikiPagesMacro',
    license      = 'GPLv3',
    zip_safe     = False,
    install_requires = 'TracAdvParseArgsPlugin>=0.2',
    keywords = 'trac list wiki page macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['traclistofwikipages.macro = traclistofwikipages.macro']}
)
