#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Abbywinters.com

from setuptools import setup, find_packages

PACKAGE = 'GridModify'
VERSION = '0.1.6'

setup(
    name=PACKAGE, version=VERSION,
    description='Allows grid modification of tickets',
    author="Abbywinters.com", author_email="trac-dev@abbywinters.com",
    maintainer = "Björn Harrtell", maintainer_email = "bjorn@wololo.org",
    license='BSD', url='http://trac-hacks.org/wiki/GridModifyPlugin',
    packages = ['gridmod'],
    package_data={
        'gridmod': [
            'htdocs/*.js',
            'htdocs/*.png',
            'htdocs/*.gif'
        ]
    },
    entry_points = {
        'trac.plugins': [
            'gridmod.web_ui = gridmod.web_ui',
        ]
    }
)
