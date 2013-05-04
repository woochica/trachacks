#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Michael Henke <michael.henke@she.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='privatecomments',
    version='0.4',
    packages=['privatecomments'],

    author='Michael Henke',
    author_email='michael.henke@she.net',
    description="A trac plugin that lets you create comments which are only visible for users with a special permission",
    license="GPL",

    keywords='trac plugin security ticket comment group',
    url='http://trac-hacks.org/wiki/PrivateCommentPlugin',

    classifiers = [
        'Framework :: Trac',
    ],

    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'privatecomments = privatecomments.privatecomments',
        ],
    },
)
