#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Bart Ogryczak
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup
import sys

name = 'BacklogPlugin'
version = '0.2.0'
min_trac_version = '0.11.1'

# Check for minimum required Trac version
try:
    import trac
    if trac.__version__ < min_trac_version:
        print "%s %s requires Trac >= %s" % (name, version, min_trac_version)
        sys.exit(1)
except ImportError:
    print "Trac not found"
    sys.exit(1)

setup(
    name=name,
    version=version,
    packages=find_packages(exclude=['*.tests']),
    author='Bart Ogryczak',
    author_email='bartlomiej.ogryczak@hyves.nl',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    url='http://trac-hacks.org/wiki/BacklogPlugin',
    license='BSD',
    description="""Organize tickets within backlogs.""",
    zip_safe=True,
    entry_points={
        'trac.plugins': [
            'backlog.db = backlog.db',
            'backlog.ticketchangelistener = backlog.ticketchangelistener',
            'backlog.web_ui = backlog.web_ui'],
    },
    package_data={
        'backlog': ['templates/*.html',
                    'htdocs/css/*.css',
                    'htdocs/css/images/*.png',
                    'htdocs/js/*.js']
    },
    test_suite='backlog.tests.test_suite',
    tests_require=[]
)

