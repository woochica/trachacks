#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'TracDragDrop',
    version = '0.11.0.8',
    description = 'Add drag-and-drop attachments feature to Trac',
    license = 'BSD', # the same as Trac
    url = 'http://trac-hacks.org/wiki/TracDragDropPlugin',
    author = 'Jun Omae',
    author_email = 'jun66j5@gmail.com',
    install_requires = ['Trac>=0.11,!=0.12-dev,<0.12'],
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'tracdragdrop' : [
            'htdocs/*.js', 'htdocs/*.css', 'htdocs/*.gif', 'templates/*.html',
        ],
    },
    entry_points = {
        'trac.plugins': [
            'tracdragdrop.web_ui = tracdragdrop.web_ui',
        ],
    }
)
