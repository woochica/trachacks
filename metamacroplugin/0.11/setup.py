#!/bin/env python

from setuptools import setup

setup(
    name='MetaMacro',
    version='0.1',
    description='Makes simple macros from wiki pages',
    maintainer='Mikhail Gusarov',
    maintainer_email='dottedmag@dottedmag.net',
    license='GPLv2+',
    packages=['metamacro'],
    entry_points={
        'trac.plugins': [
            'metamacro = metamacro'
        ],
    },
)
