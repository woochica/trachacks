#!/usr/bin/env python

from setuptools import setup
from tracserversideredirect.plugin import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = ur"$Rev$"[6:-2]
__date__     = ur"$Date$"[7:-2]

rev = max(coderev, __revision__)

setup(
    name         = 'TracServerSideRedirectPlugin',
    version      = '0.3.' + rev,
    packages     = ['tracserversideredirect'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = "Server side redirect plugin for Trac.",
    url          = 'http://www.trac-hacks.org/wiki/ServerSideRedirectPlugin',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords     = 'trac plugin server redirect',
    classifiers  = ['Framework :: Trac'],
    setup_requires = ['TracExtractUrl>=0.2.7030'],
    install_requires = ['TracExtractUrl>=0.2.7030'],
    entry_points = {'trac.plugins': ['tracserversideredirect.plugin = tracserversideredirect.plugin']}
)

