#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Max Stewart
# All rights reserved.
#
# This file is part of the TicketValidator plugin for Trac
#
# TicketValidator is free software: you can redistribute it and/or 
# modify it under the terms of the GNU General Public License as 
# published by the Free Software Foundation, either version 3 of 
# the License, or (at your option) any later version.
#
# TicketValidator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TicketValidator.  If not, see 
# <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages

setup(
    name = 'TicketValidator',
    version = '0.1',
    description = 'Ticket Validation',
    author = 'Max Stewart',
    author_email = 'max.e.stewart@gmail.com',
    license = 'BSD',
#    url = 'http://bitten.edgewall.org/',
#    download_url = 'http://bitten.edgewall.org/wiki/Download',

    zip_safe = False,

    packages = find_packages('src', exclude=['*.tests*']),
    package_dir = {'': 'src'},
    package_data = {
        'ticketvalidator': ['htdocs/*.*', 'templates/*.html']
    },
    
    entry_points = {
        'trac.plugins': [
            'ticketvalidator.admin = ticketvalidator.admin',
            'ticketvalidator.core = ticketvalidator.core',
        ],
    },
)
