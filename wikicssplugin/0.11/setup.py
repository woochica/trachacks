#!/usr/bin/env python

from setuptools import setup
from tracwikicss.plugin import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name         = 'TracWikiCssPlugin',
    version      = '0.1.' + rev,
    packages     = ['tracwikicss'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = "Wiki pages as CSS files Trac Plugin.",
    url          = 'http://www.trac-hacks.org/wiki/WikiCssPlugin',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords     = 'trac plugin wiki css',
    classifiers  = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracwikicss.plugin = tracwikicss.plugin']}
)

