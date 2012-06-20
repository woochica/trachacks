#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.from setuptools import setup

from setuptools import setup

setup(
    name='GroupTicketFields',
    version='0.0.1',
    packages=['groupticketfields'],
    package_data={
        'groupticketfields' : [
            'htdocs/*.js',
            'htdocs/*.png',
            'htdocs/css/*.css',
        ]
    },
    author = 'thomasd',
    author_email='tdoering@baumer.com',
    maintainer = 'falkb',
    maintainer_email='fbrettschneider@baumer.com',
    license = "BSD 3-Clause",
    description='Group Ticket Fields',
    long_description='Group Ticket Fields',
    keywords='Group Ticket Fields',
    entry_points = {'trac.plugins': ['groupticketfields = groupticketfields']}
)