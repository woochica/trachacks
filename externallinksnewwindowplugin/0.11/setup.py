#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'ExtLinksNewWindow',
    version = '0.1',
    description = 'Trac Load External Links in New Window',
    license = 'BSD',
    url = 'http://trac-hacks.org/wiki/ExternalLinksNewWindow',
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'extlinksnewwindow' : [ 'htdocs/*.js' ],
    },
    entry_points = {
        'trac.plugins': [
            'extlinksnewwindow = extlinksnewwindow',
        ],
    }
)
