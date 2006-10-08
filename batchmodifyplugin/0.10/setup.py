#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2006 Ashwin Phatak 

from setuptools import setup, find_packages

PACKAGE = 'BatchModify'
VERSION = '0.1.0'

setup(
    name=PACKAGE, version=VERSION,
    description='Allows batch modification of tickets',
    author="Ashwin Phatak", author_email="ashwinpphatak@gmail.com",
    license='BSD', url='http://trac-hacks.org/wiki/BatchModifyPlugin',
    packages=find_packages(exclude=['ez_setup', '*.tests*']),
    package_data={
        'batchmod': [
            'templates/*.cs'
        ]
    },
    entry_points = {
        'trac.plugins': [
            'batchmod.web_ui = batchmod.web_ui',
        ]
    }
)
