#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'teamcalendar',
    author = 'Martin Aspeli',
    author_email = 'optilude@gmail.com',
    maintainer = 'Chris Nelson',
    maintainer_email = 'Chris.Nelson@SIXNET.com',
    description = 'Trac plugin for managing team availability',
    version = '0.1',
    license='BSD',
    packages=['teamcalendar'],
    package_data={'teamcalendar': ['templates/*.html', 
                                   'htdocs/css/*.css',]},
    entry_points = {
        'trac.plugins': [
            'teamcalendar = teamcalendar'
        ]
    },
    install_requires = [
    ],
)
