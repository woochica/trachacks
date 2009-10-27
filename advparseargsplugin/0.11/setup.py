#!/usr/bin/env python

from setuptools import setup
from tracadvparseargs.parseargs import __revision__ as pluginrev
from tracadvparseargs.macro     import __revision__ as macrorev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( pluginrev, macrorev, __revision__ ) )

setup(
    name         = 'TracAdvParseArgsPlugin',
    version      = '0.1.' + rev,
    packages     = ['tracadvparseargs'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = "Advanced argument parser for Trac macros.",
    url          = 'http://www.trac-hacks.org/wiki/AdvParseArgsPlugin',
    license      = 'BSD',
    keywords     = 'trac plugin parse argument',
    classifiers  = ['Framework :: Trac'],
    entry_points = {'trac.plugins': [
          'tracadvparseargs.macro     = tracadvparseargs.macro',
          'tracadvparseargs.parseargs = tracadvparseargs.parseargs',
      ]}
)

