#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Brian P. Hinz <bphinz@users.sourceforge.net>
# All rights reserved.
#
# This software is licensed as described in the file LICENSE.txt, which
# you should have received as part of this distribution.

from setuptools import setup, find_packages
from setuptools.command import sdist
del sdist.finders[:]

PACKAGE = 'FieldGroups'
VERSION = '0.0.1'

setup(
    name = PACKAGE,
    version = VERSION,
    packages = ['fieldgroups'],
    author = 'Brian P. Hinz',
    author_email = 'bphinz@users.sourceforge.net',
    url='http://trac-hacks.org/wiki/FieldGroupsPlugin',
    description = 'Adds support for grouping custom fields in tickets',
    install_requires = ['Trac>=1.0'],
    license = '3-Clause BSD',
    zip_safe=True,
    entry_points = {
      'trac.plugins': [
        'fieldgroups.admin = fieldgroups.admin',
        'fieldgroups.api = fieldgroups.api',
        'fieldgroups.web_ui = fieldgroups.web_ui',
      ]
    },
    package_data = {
        'fieldgroups': [
            'htdocs/js/*.js',
            'htdocs/css/*.css',
            'htdocs/images/*',
            'templates/*.html', 
        ]
    },
)
