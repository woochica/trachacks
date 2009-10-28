#!/usr/bin/env python

from setuptools import setup
from tracaddheaders.plugin import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name = 'TracAddHeadersPlugin',
    version = '0.1.' + rev,
    packages = ['tracaddheaders'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = 'AddHeaders Trac Plugin.',
    url = 'http://www.trac-hacks.org/wiki/AddHeadersPlugin',
    license = 'GPLv3',
    keywords = 'trac plugin addheaders',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracaddheaders.plugin = tracaddheaders.plugin']}
)
