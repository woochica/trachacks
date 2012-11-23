#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2008 Alec Thomas
# Copyright (C) 2009-2010 Michael Renzmann
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracHacks',
    license='3-Clause BSD',
    version='2.0',
    packages=['trachacks'],
    package_data={
        'trachacks' : [
            'templates/*.html', 'htdocs/js/*.js',
            'htdocs/css/*.css', 'htdocs/*.gif',
            ]
        },
    dependency_links=[
        'http://trac-hacks.org/svn/tagsplugin/trunk#egg=TracTags-0.6',
        'http://trac-hacks.org/svn/accountmanagerplugin/trunk#egg=TracAccountManager',
        'http://trac-hacks.org/svn/voteplugin/0.11#egg=TracVote-0.1',
        'http://trac-hacks.org:81/browser/svnauthzadminplugin/0.11#egg=SvnAuthzAdminPlugin',
        ],
    entry_points={
        'trac.plugins': [
            'trachacks.web_ui = trachacks.web_ui',
            ]
        },
    install_requires=[
        'TracAccountManager',
        'TracTags >= 0.6',
        'TracVote >= 0.1',
        'SvnAuthzAdminPlugin',
        ],
    )
