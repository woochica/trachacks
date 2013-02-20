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
    name='RemoteTicketConditionalCreatePlugin',
    version='0.3.7',
    keywords='trac plugin ticket conditional remote',
    author='Zack Shahan',
    author_email='zshahan@dig-inc.net',
    url='http://trac-hacks.org/wiki/RemoteTicketConditionalCreatePlugin',
    description='Trac Remote Ticket Conditional Create Plugin',
    long_description="""
This plugin for Trac 0.12/1.0 provides Ticket escalation functionality.

Allows ticket linking via "escalating" between trac environments on same instance.
""",
    license='BSD 3-Clause',

    install_requires=['Trac >= 0.12dev', 'TracXmlRpc'],

    packages=['remoteticketconditionalcreate'],

    entry_points={
        'trac.plugins': [
            'remoteticketconditionalcreate.api = remoteticketconditionalcreate.api',
        ],
    },
)
