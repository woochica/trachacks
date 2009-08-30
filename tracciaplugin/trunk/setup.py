#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TracCia',
    version = '0.3.9',
    maintainer = 'Mikhail Gusarov',
    maintainer_email = 'dottedmag@dottedmag.net',
    url = 'http://trac-hacks.org/wiki/TracCiaPlugin',
    license = 'GPL2+',
    description = 'Trac and CIA.vc integration plugin',
    packages = ['traccia'],
    entry_points = {
        'trac.plugins': [
            'traccia = traccia',
        ],
    },
)
