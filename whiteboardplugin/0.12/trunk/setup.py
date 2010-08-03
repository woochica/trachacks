#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2010 Brian Meeker (meeker.brian@gmail.com)

from setuptools import setup, find_packages

PACKAGE = 'Whiteboard'
VERSION = '0.1.0-trac0.12'

setup(
    name=PACKAGE, version=VERSION,
    description='Gives a whiteboard view of query results',
    author="Brian Meeker", author_email="meeker.brian@gmail.com",
    license='BSD', url='http://trac-hacks.org/wiki/WhiteboardPlugin',
    packages = ['whiteboard'],
    package_data={
        'whiteboard': [
            'htdocs/js/*.js',
            'htdocs/css/*.css',
        ]
    },
    entry_points = {
        'trac.plugins': [
            'whiteboard.web_ui = whiteboard.web_ui',
        ]
    }
)
