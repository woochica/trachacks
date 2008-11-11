#!/usr/bin/env python

from setuptools import setup

setup(
    name         = 'TracExtractUrl',
    version      = '0.1',
    packages     = ['tracextracturl'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = 'Provides `extract_url` method to extract the URL from TracWiki links.',
    url          = 'http://www.trac-hacks.org/wiki/ExtractUrlPlugin',
    license      = 'BSD',
    keywords     = 'trac plugin extract url',
    classifiers  = ['Framework :: Trac'],
    zip_safe     = False,
    entry_points = {'trac.plugins': ['tracextracturl = tracextracturl']}
)

