#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]


setup(
    name         = 'TracWikiCssPlugin',
    version      = '0.2',
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

