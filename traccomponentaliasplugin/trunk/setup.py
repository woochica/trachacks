#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Zack Shahan <zshahan@dig-inc.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='TracComponentAliasPlugin',
    version='0.1.3',
    keywords='trac plugin ticket component alias',
    author='Zack Shahan',
    author_email='zshahan@dig-inc.net',
    url='http://trac-hacks.org/wiki/TracComponentAliasPlugin',
    description='Map components to friendly name.',
    long_description="""
    This plugin for Trac 1.0 and later provides a way to map
    components to a friendly name in the ticket form.
    """,
    license='BSD 3-Clause',

    install_requires=['Trac >= 0.13dev'],

    packages=['traccomponentalias'],

    entry_points={
        'trac.plugins': [
            'traccomponentalias.api = traccomponentalias.api',
        ],
    },
)
