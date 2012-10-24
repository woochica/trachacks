#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Bernhard Gruenewaldt <trac@gruenewaldt.net>
# Copyright (C) 2011-2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name = 'NikoCale',
    version = 1.0,
    author = 'yattom',
    author_email = 'yach@alles.or.jp',
    license = 'BSD',    
    url = 'http://trac-hacks.org/wiki/NikoCaleMacro',
    description = 'Macro that provides an easy-to-create Niko Niko Calendar.',
    packages = find_packages(exclude=['*.tests']),
    package_data = { 'nikocale': ['htdocs/*.png'] },
    entry_points={'trac.plugins': ['NikoCale = nikocale.macro']},
    keywords = 'trac macro',
)
