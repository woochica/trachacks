#!/usr/bin/env python

from setuptools import setup

setup(
    name         = 'TracWikiCssPlugin',
    version      = '0.1',
    packages     = ['tracwikicss'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = "Wiki pages as CSS files Trac Plugin.",
    url          = 'http://www.trac-hacks.org/wiki/WikiCssPlugin',
    license      = 'BSD',
    keywords     = 'trac plugin wiki css',
    classifiers  = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracwikicss.plugin = tracwikicss.plugin']}
)

