#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracAddHeadersPlugin',
    version = '0.1',
    packages = ['tracaddheaders'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = 'AddHeaders Trac Plugin.',
    url = 'http://www.trac-hacks.org/wiki/AddHeadersPlugin',
    license = 'GPLv3',
    keywords = 'trac plugin addheaders',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracaddheaders.plugin = tracaddheaders.plugin']}
)
