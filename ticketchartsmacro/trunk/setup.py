#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2009 Aviram C <aviramc@gmail.com>
# Copyright (c) 2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

setup(
    name='TracTicketCharts',
    version='0.2',
    author='Aviram C',
    author_email='aviramc@gmail.com',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    description="""Make various types of charts regarding the number of
        tickets using OpenFlashChart2.""",
    license='?',
    packages=find_packages(exclude=['*.tests']),
    entry_points="""
        [trac.plugins]
        ticketcharts = ticketcharts.TicketCharts
    """,
    install_requires=['Trac >= 0.11', 'TracAdvParseArgsPlugin'],
    package_data={'ticketcharts': [
        'htdocs/*.swf',
        'htdocs/js/*.js']
    },
)
