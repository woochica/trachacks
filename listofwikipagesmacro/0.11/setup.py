#!/usr/bin/env python

from setuptools import setup
from traclistofwikipages.macro import __revision__ as macrorev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = r"$Rev$"[6:-2]
__date__     = r"$Date$"[7:-2]

rev = max(__revision__, macrorev)

setup(
    name = 'TracListOfWikiPagesMacro',
    version = '0.3.' + rev,
    packages = ['traclistofwikipages'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    package_data = {
        'traclistofwikipages' : [ 'htdocs/*.css' ],
    },
    description = "ListOfWikiPagesMacro Trac Macro.",
    url = 'http://www.trac-hacks.org/wiki/ListOfWikiPagesMacro',
    license      = 'GPLv3',
    zip_safe     = False,
    install_requires = 'TracAdvParseArgsPlugin>=0.2',
    keywords = 'trac list wiki page macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['traclistofwikipages.macro = traclistofwikipages.macro']}
)
