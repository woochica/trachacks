#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.

from setuptools import setup, find_packages

setup(
    name = 'TracExcelViewer', version = '0.1',
    author = 'Christopher Lenz', author_email = 'cmlenz@gmx.de',
    url = 'http://trac-hacks.swapoff.org/wiki/ExcelViewer',
    description = 'Support for preview of Microsoft Excel files in Trac',
    license = 'BSD',
    packages = find_packages(exclude=['*.tests*']),
    entry_points = {
        'trac.plugins': ['excelviewer = tracexcelviewer']
    },
    install_requires = ['xlrd'],
    zip_safe = True
)
