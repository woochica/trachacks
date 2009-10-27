#!/usr/bin/env python

from setuptools import setup
from tracgooglemap.macro import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name = 'TracGoogleMapMacro',
    version = '0.5.' + rev,
    packages = ['tracgooglemap'],
    author = 'Martin Scharrer',
    package_data = {
        'tracgooglemap' : [ 'htdocs/*.js' ],
    },
    author_email = 'martin@scharrer-online.de',
    description = "GoogleMap Trac Macro.",
    url = 'http://www.trac-hacks.org/wiki/GoogleMapMacro',
    license = 'GPLv3',
    keywords = 'trac googlemap macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracgooglemap.macro = tracgooglemap.macro']}
)
