#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2010 Brian Meeker (meeker.brian@gmail.com)

import os
from setuptools import setup, find_packages

PACKAGE = 'whiteboard'
VERSION = '0.1.0-trac0.12'

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name=PACKAGE, version=VERSION,
    description='Gives a whiteboard view of query results',
    long_description=read('README'),
    author="Brian Meeker", author_email="meeker.brian@gmail.com",
    maintainer='Olemis Lang', maintainer_email='olemis+trac@gmail.com',
    license='BSD', url='http://trac-hacks.org/wiki/WhiteboardPlugin',
    packages = ['whiteboard'],
    package_data={
        'whiteboard': [
            'templates/*.html',
            'htdocs/js/*.js',
            'htdocs/css/*.css'
        ]
    },
    entry_points = {
        'trac.plugins': [
            'whiteboard.web_ui = whiteboard.web_ui',
        ]
    }
)
