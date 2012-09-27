#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'EstimationTools',
    author = 'Joachim Hoessler',
    author_email = 'hoessler@gmail.com',
    description = 'Trac plugin for visualizing and quick editing of effort estimations',
    version = '0.4.6',
    license='BSD',
    packages=['estimationtools'],
    package_data = { 'estimationtools': ['htdocs/*.js', 'templates/*.html'] },
    entry_points = {
        'trac.plugins': [
            'estimationtools = estimationtools'
        ]
    },
    test_suite = 'estimationtools.tests.test_suite',
    tests_require = []
)
