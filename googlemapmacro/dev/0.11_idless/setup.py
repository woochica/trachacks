#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'GoogleMapMacro',
    version = '0.1',
    packages = ['googlemap'],
    author = 'Martin Scharrer',
    package_data = {
        'googlemap' : [ 'htdocs/*.js' ],
    },
    author_email = 'martin@scharrer-online.de',
    description = "GoogleMap Trac Macro.",
    url = 'http://www.trac-hacks.org/wiki/GoogleMapMacro',
    license = 'GPLv3',
    keywords = 'trac plugin googlemap macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['googlemap.macro = googlemap.macro']}
)
