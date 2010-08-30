#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]


setup(
    name         = 'TracDashesSyntaxPlugin',
    version      = '1.0',
    packages     = ['tracdashessyntax'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = "Trac Plug-in to add Wiki syntax for em and en dashes.",
    url          = 'http://www.trac-hacks.org/wiki/DashesSyntaxPlugin',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords     = 'trac plugin wiki syntex dash em en',
    classifiers  = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracdashessyntax.plugin = tracdashessyntax.plugin']}
)
