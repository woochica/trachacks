#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup

setup(
    name = 'TracSentinel',
    version = '0.1',
    packages = ['tracsentinel'],

    author = 'Thomas Gish',
    author_email = 'tgish@thomasgish.us',
    description = 'A modified authentication plugin to use the MSU Sentinel system.',
    license = 'BSD',
    keywords = 'trac 0.11 plugin sentinel authentication',

    install_requires = ['Trac', 'ZSI'],

    entry_points = {
        'trac.plugins': [
            'tracsentinel.tracsentinel = tracsentinel.tracsentinel'
        ]
    }
)
