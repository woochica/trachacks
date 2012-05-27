#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

extra = {}

setup(
    name = 'OverlayView',
    version = '0.12.0.3',
    description = 'Provides an overlay view to view attachments',
    license = 'BSD', # the same as Trac
    url = 'http://trac-hacks.org/wiki/OverlayViewPlugin',
    author = 'Jun Omae',
    author_email = 'jun66j5@gmail.com',
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'tracoverlayview': ['htdocs/*.*', 'templates/*.html'],
    },
    entry_points = {
        'trac.plugins': [
            'tracoverlayview.web_ui = tracoverlayview.web_ui',
        ],
    },
    **extra)
