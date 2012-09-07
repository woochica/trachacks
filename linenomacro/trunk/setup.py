#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Adamansky Anton <anton@adamansky.com>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name = 'Lineno',
    version = '1.2',
    author = 'Adamansky Anton',
    author_email = 'anton@adamansky.com',
    description = 'Prints line numbered code listings',
    license = 'Apache License, Version 2.0',
    url = 'http://trac-hacks.org/wiki/LinenoMacro',
    packages = find_packages(exclude=['tests*']),
    package_data = { 'lineno' : [ 'htdocs/css/*.css' ] },
    entry_points = """
        [trac.plugins]
        lineno = lineno.LinenoMacro
    """,
)
