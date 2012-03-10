#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Daniel Rolls, Maxeler Technologies Inc <drolls@maxeler.com>  
# Derived from Christopher Lenz's ExcelViewerPlugin 
#   Copyright (C) 2006 Christopher Lenz <cmlenz@gmx.de>
#   All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup, find_packages

setup(
    name = 'TracExcelXLSTViewer', version = '0.9.2',
    author = 'Daniel Rolls', author_email = 'drolls@maxeler.com',
    description = 'Support for preview of Microsoft Excel XLST files in Trac',
    license = 'BSD',
    packages = find_packages(exclude=['*.test*']),
    entry_points = {
        'trac.plugins': ['excelXLSTviewer = tracexcelxlstviewer']
    },
    install_requires = ['openpyxl'],
    zip_safe = True
)

