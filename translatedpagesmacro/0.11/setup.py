#!/bin/env python

from setuptools import setup

PACKAGE = 'TranslatedPages'

setup(
    name=PACKAGE,
    version='0.3',
    packages=['translatedpages'],
    entry_points={
        'trac.plugins': [
            '%s = translatedpages' % PACKAGE
        ],
    },
)
