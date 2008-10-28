#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'gchartplugin',
    author = 'Martin Aspeli',
    author_email = 'optilude@gmail.com',
    description = 'Trac plugin for drawing charts with Google Chart API',
    version = '0.1',
    license='BSD',
    packages=['gchartplugin'],
    package_data = { 'gchartplugin': [] },
    entry_points = {
        'trac.plugins': [
            'gchartplugin = gchartplugin'
        ]
    },
    install_requires = [
        'google-chartwrapper',
    ],
)
