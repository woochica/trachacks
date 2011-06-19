#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'SharingButtonsPlugin',
    version = '0.12.0.1',
    description = 'Add Sharing Buttons to Your Trac',
    license = 'BSD', # the same license as Trac
    url = 'http://trac-hacks.org/wiki/SharingButtonsPlugin',
    author = 'Jun Omae',
    author_email = 'jun66j5@gmail.com',
    packages = find_packages(exclude=['*.tests*']),
    entry_points = {
        'trac.plugins': [
            'tracsharingbuttons.filter = tracsharingbuttons.filter',
        ],
    },
)
