#!/usr/bin/env python

from setuptools import setup
from tracadvparseargs.parseargs import __revision__ as revision

version = '0.1'

setup(
    name         = 'TracAdvParseArgsPlugin',
    version      = version + '.' + revision,
    packages     = ['tracadvparseargs'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = "Advanced argument parser for Trac macros.",
    url          = 'http://www.trac-hacks.org/wiki/AdvParseArgsPlugin',
    license      = 'BSD',
    keywords     = 'trac plugin parse argument',
    classifiers  = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracadvparseargs = tracadvparseargs']}
)

