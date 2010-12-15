#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>


from setuptools import setup

setup(
    name='TaskList',
    version='0.1.2',
    packages=['tasklist'],
    author='John Hampton',
    description='Provides a task list based on tickets.  Allows for very simple ticket creation',
    url='http://trac-hacks.org/wiki/TaskListPLugin',
    license='BSD',
    entry_points = {
        'trac.plugins': [
            'tasklist = tasklist.main',
        ]
    },
    package_data = {
        'tasklist' : [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'templates/*.html',
        ]
    }
)
