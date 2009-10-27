#!/usr/bin/env python

# $Id$
# $URL$

from setuptools import setup
from tracnumberedheadlines.plugin import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name = 'TracNumberedHeadlinesPlugin',
    version = '0.3.' + rev,
    packages = ['tracnumberedheadlines'],
    author = 'Martin Scharrer',
    package_data = {
        'tracnumberedheadlines' : [ 'htdocs/*.css' ],
    },
    author_email = 'martin@scharrer-online.de',
    description = "Trac Plug-in to add numbered headlines.",
    url = 'http://www.trac-hacks.org/wiki/NumberedHeadlinesPlugin',
    license = 'BSD',
    keywords = 'trac numbered headlines plugin',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracnumberedheadlines.plugin = tracnumberedheadlines.plugin']}
)
