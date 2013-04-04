#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2012 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
from setuptools import setup

setup(
    name='TracMasterTickets',
    version='3.0.5',
    packages=['mastertickets'],
    package_data={
        'mastertickets': [
            'htdocs/img/*.gif',
            'htdocs/img/*.png',
            'htdocs/js/*.js',
            'htdocs/css/*.css',
            'templates/*.html'
        ]
    },

    author='Noah Kantrowitz',
    author_email='noah@coderanger.net',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    description='Provides support for ticket dependencies and master tickets.',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license='BSD 3-Clause',
    keywords='trac plugin ticket dependencies master',
    url='http://trac-hacks.org/wiki/MasterTicketsPlugin',
    classifiers=[
        'Framework :: Trac',
        #'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],

    install_requires=['Trac>=0.12'],

    test_suite='mastertickets.tests.suite',
    entry_points={
        'trac.plugins': [
            'mastertickets.api = mastertickets.api',
            'mastertickets.web_ui = mastertickets.web_ui',
        ]
    }
)
