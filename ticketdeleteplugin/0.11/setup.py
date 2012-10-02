#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup
from ticketdelete import assert_trac_version

name = 'TracTicketDelete'

assert_trac_version('< 0.12', name)

setup(
    name=name,
    version='3.0.0',
    author="Noah Kantrowitz",
    author_email="noah@coderanger.net",
    maintainer="Ryan J Ollos",
    maintainer_email="ryan.j.ollos@gmail.com",
    description="Remove tickets and ticket changes from Trac.",
    long_description="Provides a web interface to removing whole tickets and ticket changes in Trac.",
    license="3-Clause BSD",
    keywords="trac plugin ticket delete",
    url="http://trac-hacks.org/wiki/TicketDeletePlugin",
    classifiers=[
        'Framework :: Trac',
    ],
    packages=find_packages(exclude=['*.tests*']),
    package_data={ 'ticketdelete': ['templates/*.html'] },
    entry_points={
        'trac.plugins': [
            'ticketdelete = ticketdelete.web_ui'
        ]
    }
)
