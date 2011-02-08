#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]


setup(
    name = 'TracAddHeadersPlugin',
    version = '0.3',
    packages = ['tracaddheaders'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = 'AddHeaders Trac Plugin.',
    url = 'http://www.trac-hacks.org/wiki/AddHeadersPlugin',
    license = 'GPLv3',
    zip_safe     = False,
    keywords = 'trac plugin addheaders',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracaddheaders.plugin = tracaddheaders.plugin']}
)
