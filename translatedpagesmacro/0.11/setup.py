#!/bin/env python

from setuptools import setup

setup(
    name='TranslatedPagesMacro',
    version='0.3',
    maintainer='Mikhail Gusarov',
    maintainer_email='dottedmag@dottedmag.net',
    url='http://trac-hacks.org/wiki/TranslatedPagesMacro',
    packages=['translatedpages'],
    entry_points={
        'trac.plugins': [
            'TranslatedPagesMacro = translatedpages'
        ],
    },
)
