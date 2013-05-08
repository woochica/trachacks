#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Michael Henke <michael.henke@she.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='hideable_query',
    version='0.2',
    packages=['hideable_query'],

    author='Michael Henke',
    author_email='michael.henke@she.net',
    description=""""A trac plugin that lets you hide the query site and
                    the links to it""",
    license="BSD 3-Clause",

    keywords='trac plugin security hide query report',
    url='http://trac-hacks.org/wiki/HideableQueryPlugin',

    classifiers=[
        'Framework :: Trac',
    ],

    install_requires=['Trac'],

    entry_points={
        'trac.plugins': [
            'hideable_query = hideable_query',
        ],
    },
)
