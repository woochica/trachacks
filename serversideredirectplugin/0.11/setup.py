#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]


setup(
    name         = 'TracServerSideRedirectPlugin',
    version      = '0.4',
    packages     = ['tracserversideredirect'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = "Server side redirect plugin for Trac.",
    url          = 'http://www.trac-hacks.org/wiki/ServerSideRedirectPlugin',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords     = 'trac plugin server redirect',
    classifiers  = ['Framework :: Trac'],
    install_requires = ['TracExtractUrl>=0.2.7030'],
    entry_points = {'trac.plugins': ['tracserversideredirect.plugin = tracserversideredirect.plugin']}
)

