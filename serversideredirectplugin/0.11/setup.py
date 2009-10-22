#!/usr/bin/env python

from setuptools import setup
from tracserversideredirect.plugin import __revision as revision

setup(
    name         = 'TracServerSideRedirectPlugin',
    version      = '0.2.' + revision,
    packages     = ['tracserversideredirect'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = "Server side redirect plugin for Trac.",
    url          = 'http://www.trac-hacks.org/wiki/ServerSideRedirectPlugin',
    license      = 'BSD',
    keywords     = 'trac plugin server redirect',
    classifiers  = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracserversideredirect.plugin = tracserversideredirect.plugin']}
)

