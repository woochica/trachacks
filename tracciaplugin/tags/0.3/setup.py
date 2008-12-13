#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TracCia',
    version = '0.3',
    packages = ['traccia'],
    entry_points = {
        'trac.plugins': [
            'traccia = traccia',
        ],
    },
)
