#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracGoogleMapMacro',
    version = '0.5',
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
