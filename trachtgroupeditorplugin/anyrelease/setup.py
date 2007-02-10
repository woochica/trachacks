#!/usr/bin/env python
#
# Copyright (C) 2007 Chris Liechti <cliechti@gmx.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. It is the
# new BSD license.

from setuptools import setup

setup(
    name = 'TracHtGroupEditor',
    version = '1.0',
    author = 'Chris Liechti',
    author_email = 'cliechti@gmx.net',
    url = 'http://trac-hacks.org/wiki/TracHtGroupEditorPlugin',
    description = 'HTGroup file management plugin for Trac',
    license = 'BSD',

    zip_safe=True,
    packages=['htgroups_edit'],
    package_data={'htgroups_edit': ['templates/*.cs']},

    install_requires = [
        'TracWebAdmin',
    ],

    entry_points = {
        'trac.plugins': [
            'htgroups_edit.admin = htgroups_edit.admin',
        ]
    },

    #~ test_suite = 'htgroups_edit.tests.suite',
)

