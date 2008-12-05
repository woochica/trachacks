#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup

setup(
    name = 'TracProtected',
    version = '1.0.1',
    packages = ['protected'],
    package_data = {"protected":[]},
    author = 'Boudewijn Schoon',
    author_email = 'boudewijn@frayja.com',
    description = 'A Trac macro to limit access to parts of a trac page.',
    long_description = 'A Trac macro to limit access to parts of a trac page.',
    license = 'BSD',
    keywords = 'trac macro authentication protected access',
    url = '',
    classifiers = ['Framework :: Trac',
                   'Development Status :: 5 - Production/Stable',
                   'Environment :: Web Environment',
                   'License :: OSI Approved :: BSD License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   ],
    install_requires = ['Trac'],
    entry_points = {'trac.plugins': ['protected.macro = protected.macro',],},
)
