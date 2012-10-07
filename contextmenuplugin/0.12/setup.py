#!/usr/bin/env python
# coding: utf-8
#
# Copyright (c) 2010, Logica
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

setup(
    name = 'ContextMenuPlugin',
    version = '0.2',
    author = 'Pontus Enmark',
    author_email = 'pontus.enmark@logica.com',
    description = "Drop down menu for the Source Browser.",
    license = "Copyright (c) 2010, Logica. All rights reserved. Released under the 3-clause BSD license.",
    url = "http://trac-hacks.org/wiki/ContextMenuPlugin",
    packages = find_packages(exclude=['*.tests']),
    package_data = {'contextmenu': [
        'htdocs/*.js',
        'htdocs/*.css'
        ]
    },
    install_requires = [],
    tests_require = ['nose'],
    test_suite = 'nose.collector',
    entry_points = {
        'trac.plugins': [
            'contextmenu.contextmenu = contextmenu.contextmenu',
        ]
    }
)
