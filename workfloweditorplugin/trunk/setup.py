#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Takanori Suzuki <takanorig@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

setup(
    name='WorkflowEditorPlugin',
    version='1.1.6',
    description="Edit Ticket Workflow",
    url="http://trac-hacks.org/wiki/WorkflowEditorPlugin",
    author="Takanori Suzuki",
    author_email="takanorig@gmail.com",
    license="3-Clause BSD",
    zip_safe=True,
    packages=find_packages(exclude=['*.tests*']),
    entry_points={
        'trac.plugins': [
            'workfloweditor.workfloweditor_admin = workfloweditor.workfloweditor_admin',
        ]
    },
    package_data={
        'workfloweditor': [
            'templates/*.html',
            'templates/*.ini',
            'htdocs/css/*.css',
            'htdocs/images/*.*',
            'htdocs/js/*.js',
            'htdocs/js/grid/*.js',
            'htdocs/js/ui/*.js',
        ]
    }
)
