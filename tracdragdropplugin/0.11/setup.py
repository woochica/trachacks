#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'TracDragDrop',
    version = '0.11.0.4',
    description = 'Add drag-and-drop attachments feature to Trac',
    license = 'BSD',
    url = 'http://trac-hacks.org/wiki/TracDragDropPlugin',
    author = 'Jun Omae',
    author_email = 'jun66j5@gmail.com',
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'tracdragdrop' : [ 'htdocs/*.js', 'htdocs/*.css', 'templates/*.html' ],
    },
    entry_points = {
        'trac.plugins': [
            'tracdragdrop = tracdragdrop.web_ui',
        ],
    }
)
