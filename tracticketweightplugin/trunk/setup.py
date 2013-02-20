#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2012 Zack Shahan <zshahan@dig-inc.net>
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='tracticketweightPlugin',
    version='0.1.3',
    keywords='trac plugin ticket weight',
    author='Zack Shahan',
    author_email='zshahan@dig-inc.net',
    url='http://trac-hacks.org/wiki/TracTicketWeightPlugin',
    description='Trac Ticket Weight Plugin',
    long_description="""

""",
    license='BSD 3-Clause',

    install_requires=['Trac >= 0.12dev'],

    packages=['tracticketweight'],

    entry_points={
        'trac.plugins': [
            'tracticketweight.api = tracticketweight.api',
        ],
    },
)
