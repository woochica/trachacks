#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Max Stewart <max.e.stewart@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup, find_packages

setup(
    name = 'TicketValidator',
    version = '0.2',
    description = 'Ticket Validation',
    author = 'Max Stewart',
    author_email = 'max.e.stewart@gmail.com',
    license = '3-Clause BSD',
    url = 'http://trac-hacks.org/wiki/TicketValidatorPlugin',

    zip_safe = False,

    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'ticketvalidator': ['templates/*.html']
    },
    
    entry_points = {
        'trac.plugins': [
            'ticketvalidator.admin = ticketvalidator.admin',
            'ticketvalidator.core = ticketvalidator.core',
        ],
    },
)
