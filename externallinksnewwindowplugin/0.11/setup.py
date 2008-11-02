#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'TracExtLinksNewWindow',
    version = '0.2',
    description = 'Trac Load External Links in New Window',
    license = 'GPLv3',
    url = 'http://trac-hacks.org/wiki/ExternalLinksNewWindow',
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    packages = ['tracextlinksnewwindow'],
    package_data = {
        'tracextlinksnewwindow' : [ 'htdocs/*.js' ],
    },
    entry_points = {
        'trac.plugins': [
            'tracextlinksnewwindow = tracextlinksnewwindow',
        ],
    }
)
