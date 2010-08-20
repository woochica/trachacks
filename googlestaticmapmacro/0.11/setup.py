#!/usr/bin/env python

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name = 'TracGoogleStaticMapMacro',
    version = '0.4',
    packages = ['tracgooglestaticmap'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "GoogleStaticMap Trac Macro.",
    url = 'http://www.trac-hacks.org/wiki/GoogleStaticMapMacro',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords = 'trac google static map macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracgooglestaticmap.macro = tracgooglestaticmap.macro']}
)
