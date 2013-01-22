#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Chris Liechti <cliechti@gmx.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. It is the
# new BSD license.

from setuptools import setup

setup(
    name = 'PageAuthzPolicyEditor',
    version = '0.12',
    author = 'Robert Martin',
    author_email = 'robert.martin@arqiva.com',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryan.j.ollos@gmail.com',
    url = '',
    description = 'Page Authz File management plugin for Trac',
    license = '3-Clause BSD',

    zip_safe=True,
    packages=['page_authz_policy_editor'],
    package_data={'page_authz_policy_editor': ['templates/*.html']},
    entry_points = {
        'trac.plugins': [
            'page_authz_policy_editor.admin = page_authz_policy_editor.pape_admin',
        ]
    },
     install_requires = ['Trac >=0.11', 'configobj'],
)

