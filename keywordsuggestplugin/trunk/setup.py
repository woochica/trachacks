#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Polar Technologies - www.polartech.es
# Copyright (C) 2010 Alvaro J Iradier
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='TracKeywordSuggest',
    version = '0.5.0',
    author = 'Dmitry Dianov',
    author_email = 'scratcha at google mail',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryan.j.ollos@gmail.com',
    description = "Add suggestions to ticket 'keywords' field",
    license = "BSD 3-Clause",
    url = 'http://trac-hacks.org/wiki/KeywordSuggestPlugin',
    packages=find_packages(exclude=['*.tests*']),
    package_data = { 'keywordsuggest': ['htdocs/js/*.js','htdocs/css/*.css','htdocs/images/*.png'] },
    entry_points = {
        'trac.plugins': [
            'keywordsuggest = keywordsuggest.keywordsuggest'
        ]
    }
)
