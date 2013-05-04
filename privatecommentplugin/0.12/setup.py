#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Michael Henke <michael.henke@she.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

setup(
    name='PrivateComments',
    version='0.4',
    packages=find_packages(),

    author='Michael Henke',
    author_email='michael.henke@she.net',
    description="""A trac plugin that lets you create comments which are
        only visible for users with a special permission""",
    license="BSD 3-Clause",

    keywords='trac plugin security ticket comment group',
    url='http://trac-hacks.org/wiki/PrivateCommentPlugin',

    classifiers=[
        'Framework :: Trac',
    ],

    install_requires=['Trac'],

    entry_points={
        'trac.plugins': [
            'PrivateComments = privatecomments.privatecomments',
        ],
    },
)
