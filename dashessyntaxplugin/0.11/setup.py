#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracDashesSyntaxPlugin',
    version = '0.1',
    packages = ['tracdashessyntax'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "Trac Plug-in to add Wiki syntax for em and en dashes.",
    url = 'http://www.trac-hacks.org/wiki/DashesSyntaxPlugin',
    license = 'BSD',
    keywords = 'trac plugin wiki syntex dash em en',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracdashessyntax.plugin = tracdashessyntax.plugin']}
)
