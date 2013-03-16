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
    name='TracTicketConditionalValidateFieldsPlugin',
    version='0.1.0',
    keywords='trac plugin ticket validate field',
    author='Zack Shahan',
    author_email='zshahan@dig-inc.net',
    url='http://trac-hacks.org/wiki/TracTicketConditionalValidateFieldsPlugin',
    description='Validates fields based on ticket type.',
    long_description="""
    This plugin for Trac 1.0 and later provides validation of ticket fields based off
    if the ticket is a defect,enhancement,etc.
    """,
    license='BSD 3-Clause',

    install_requires=['Trac >= 0.13dev'],

    packages=['tracticketconditionalvalidatefield'],

    entry_points={
        'trac.plugins': [
            'tracticketconditionalvalidatefield.api = tracticketconditionalvalidatefield.api',
        ],
    },
)
