#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Radu Gasler <miezuit@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os

from setuptools import setup

setup(
    name = 'TracWikiReplace',
    version = '1.1.1',
    packages = ['wikireplace'],
    package_data = {'wikireplace': ['templates/*.html']},

    author = 'Radu Gasler',
    author_email = 'miezuit@gmail.com',
    description = 'Add simple support for replacing text in wiki pages',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = '3-Clause BSD',
    keywords = 'trac 0.11 plugin wiki page search replace',
    url = 'http://trac-hacks.org/wiki/WikiReplacePlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac'],
    
    entry_points = {
        'trac.plugins': [
            'wikireplace.web_ui = wikireplace.web_ui',
        ],
        'console_scripts': [
            'trac-wikireplace = wikireplace.script:run'
        ],
    },
)
