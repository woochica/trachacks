#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'CKIntegration',
    version = '1.0dev',
    description = 'CKEditor integration for Trac',
    author = 'Itamar Ostricher, Edan Maor',
    author_email = 'itamarost@gmail.com, edanm@btlms.com',
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'ckintegration' : ['htdocs/*.js'],

    },
    entry_points = {
        'trac.plugins': [
            'ckintegration = ckintegration',
        ],
    }
)
