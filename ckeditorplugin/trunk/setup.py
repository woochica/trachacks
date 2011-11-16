#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'CKIntegration',
    version = '1.1dev',
    description = 'CKEditor integration for Trac',
    author = 'Itamar Ostricher, Edan Maor, Franz Mayer',
    author_email = 'itamarost@gmail.com, edanm@btlms.com, franz.mayer@gefasoft.de',
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'ckintegration' : ['htdocs/*.js', 'htdocs/images/*.png'],

    },
    entry_points = {
        'trac.plugins': [
            'ckintegration = ckintegration',
        ],
    }
)
