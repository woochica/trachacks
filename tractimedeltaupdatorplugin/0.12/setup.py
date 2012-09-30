#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'TracTimeDeltaUpdator',
    version = '0.12.0.1',
    description = 'Automatically updating for relative date/time displays on Trac',
    license = 'BSD', # the same as Trac
    url = 'http://trac-hacks.org/wiki/TracTimeDeltaUpdatorPlugin',
    author = 'Jun Omae',
    author_email = 'jun66j5@gmail.com',
    install_requires = ['Trac >= 0.12'],
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'tractimedeltaupdator' : [
            'htdocs/*.js',
        ],
    },
    entry_points = {
        'trac.plugins': [
            'tractimedeltaupdator.web_ui = tractimedeltaupdator.web_ui',
        ],
    },
)
