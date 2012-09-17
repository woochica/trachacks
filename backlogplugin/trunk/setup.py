#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Bart Ogryczak
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='BacklogPlugin',
    version='0.2.0',
    packages=['backlog'],
    author='Bart Ogryczak',
    author_email='bartlomiej.ogryczak@hyves.nl',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    url='http://trac-hacks.org/wiki/BacklogPlugin',
    license='BSD',
    description="""Allows multiple backlogs """,
    zip_safe=True,
    entry_points={
        'trac.plugins': ['backlog.db = backlog.db',
                         'backlog.ticketchangelistener = backlog.ticketchangelistener',
                         'backlog.web_ui = backlog.web_ui'],
    },
    package_data={
        'backlog': ['templates/*.html',
                    'htdocs/css/*.css',
                    'htdocs/js/*.js',
                    'htdocs/images/*']
    },
)

