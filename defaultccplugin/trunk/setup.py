#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 ERCIM
# Copyright (C) 2009 Jean-Guilhem Rouel <jean-guilhem.rouel@ercim.org>
# Copyright (C) 2009 Vivien Lacourba <vivien.lacourba@ercim.org>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name = 'DefaultCc',
    version = '0.3',
    packages = ['defaultcc'],
    include_package_data = True,
    author = "Jean-Guilhem Rouel",
    author_email = "jean-guilhem.rouel@ercim.org",
    maintainer="Ryan J Ollos",
    maintainer_email="ryan.j.ollos@gmail.com",
    description = "Automatically adds a default CC list to new tickets.",
    long_description = "Automatically adds a default CC list when a new ticket is created," \
        "based on its initial component." \
        "CC lists can be configured per component through the component admin UI",
    license = "3-Clause BSD",
    keywords = "trac CC ticket component",
    url = "http://trac-hacks.org/wiki/DefaultCCPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    entry_points = {
        'trac.plugins': [
            'defaultcc.admin = defaultcc.admin',
            'defaultcc.main = defaultcc.main'
        ],
    },
    zip_safe = True
)
