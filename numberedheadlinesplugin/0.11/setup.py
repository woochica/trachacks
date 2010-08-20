#!/usr/bin/env python

# $Id$
# $URL$

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name = 'TracNumberedHeadlinesPlugin',
    version = '0.4',
    packages = ['tracnumberedheadlines'],
    author = 'Martin Scharrer',
    package_data = {
        'tracnumberedheadlines' : [ 'htdocs/*.css' ],
    },
    author_email = 'martin@scharrer-online.de',
    description = "Trac Plug-in to add numbered headlines.",
    url = 'http://www.trac-hacks.org/wiki/NumberedHeadlinesPlugin',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords = 'trac numbered headlines plugin',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracnumberedheadlines.plugin = tracnumberedheadlines.plugin']}
)
