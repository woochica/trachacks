#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Robert Martin <robert.martin@arqiva.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

setup(
    name='TracHtGroupEditorPlugin',
    version='2.1',
    author='Robert Martin',
    author_email='robert.martin@arqiva.com',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    description='HT Group Editor plugin for Trac',
    url='http://trac-hacks.org/wiki/HtGroupEditorPlugin',
    license='GPL',
    packages=find_packages(exclude=['*.tests*']),
    entry_points={
        'trac.plugins': ['HtGroupEditor = htgroupeditor.htgroupeditor']
    },
    package_data={'htgroupeditor': ['templates/*.html',
                                    'htdocs/css/*.css']},
    install_requires=['Trac >=0.11', 'configobj'],
)
