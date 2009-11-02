#!/usr/bin/env python

from setuptools import setup
from tracdashessyntax.plugin import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

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
