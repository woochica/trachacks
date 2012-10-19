#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Ryan J Ollos
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='Wikinfo',
    version='0.2',
    packages=['wikinfo'],
    package_data={},
    author="Ryan J Ollos",
    author_email="ryan.j.ollos@gmail.com",
    description="Provides a few useful macros to get data about wiki pages",
    license="3-Clause BSD",
    keywords="trac wiki info macro",
    url="http://trac-hacks.org/WikinfoPlugin",
    entry_points={
        'trac.plugins': [
            'wikinfo.macro = wikinfo.macro'
        ]
    }
)

