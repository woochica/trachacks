#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Date:         Mon Jun 22 12:39:48 MDT 2009
# Copyright:    2009 CodeRage
# Author:       Jonathan Turkanis
# 
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

import os

from setuptools import setup

setup(
    name = 'TracAccess',
    version = '0.1',
    packages = ['access'],
    package_data = {"access":[]},
    author = 'Jonathan Turkanis',
    author_email = 'turkanis@coderage.com',
    url='http://trac-hacks.org/wiki/AccessMacro',
    description = "A Trac macro to display or hide parts of wiki pages based on permissions",
    long_description = '''The Trac Access macro allows parts of wiki pages to be displayed or 
        hidden depending on the permissions of the current user. It has two 
        variants: the first makes a block of wiki text visible only by users 
        with one of a specified list of permissions, and the second hides a 
        block of wiki text for users with one of a specified list of permissions. 
        
        Examples:

        {{{
        #!access
        #allow(TICKET_ADMIN, MILESTONE_ADMIN)

        This is seen only by users with one of the permissions TICKET_ADMIN or MILESTONE_ADMIN
        }}}

        {{{
        #!access
        #deny(REPORT_VIEW)

        This is seen only by users who do not have the REPORT_VIEW permission
        }}}

        [[access(deny(REPORT_VIEW), This is an alternate syntax)]]

        }}}
    ''',
    license = 'BSL1.0',
    keywords = 'trac macro permissions turkanis',
    classifiers = ['Framework :: Trac',
                   'Development Status :: 3 - Alpha',
                   'Environment :: Web Environment',
                   'License :: OSI Approved :: Boost Software License 1.0',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   ],
    install_requires = ['Trac'],
    entry_points = {'trac.plugins': ['access.macro = access.macro',],},
)
