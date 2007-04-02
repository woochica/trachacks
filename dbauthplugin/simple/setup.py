#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'TracDbAuth',
    version = '0.4',
    description = 'DB-based authentication for Trac',
    license = 'MIT',
    author = 'Waldemar Kornewald',
    url = 'http://haiku-os.org',

    packages = find_packages(exclude=['ez_setup', '*.tests*']),
    package_data = {
        'dbauth': [
            'htdocs/css/*.css',
            'htdocs/img/*.png',
            'htdocs/js/*.js',
            'templates/*.html',
            'templates/*.txt'
        ]
    },
    entry_points = {
        'trac.plugins': [
            'dbauth.auth = dbauth.auth'
        ]
    }
)
