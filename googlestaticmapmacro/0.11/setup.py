#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracGoogleStaticMapMacro',
    version = '0.2',
    packages = ['tracgooglestaticmap'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "GoogleStaticMap Trac Macro.",
    url = 'http://www.trac-hacks.org/wiki/GoogleStaticMapMacro',
    license = 'GPLv3',
    keywords = 'trac google static map macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracgooglestaticmap.macro = tracgooglestaticmap.macro']}
)
