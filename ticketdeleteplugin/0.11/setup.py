#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='TracTicketDelete',
    version='3.0.0',
    packages=['ticketdelete'],
    package_data={ 'ticketdelete': ['templates/*.html'] },
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
    entry_points={
        'trac.plugins': [
            'ticketdelete = ticketdelete.web_ui'
        ]
    }
)
