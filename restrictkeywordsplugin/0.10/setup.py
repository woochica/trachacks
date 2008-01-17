#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Thomas Tressières <thomas.tressieres@free.fr>
# All rights reserved.
#

from setuptools import setup, find_packages

setup(
    name='TracRestrictKeywords',
    version = '0.1',
    description = "A plugin to restrict keywords filed in Trac's Ticket",
    author = 'Thomas Tressières',
    author_email = 'thomas.tressieres@free.fr',
    license='GPL',
    url='http://trac-hacks.org/wiki/RestrictKeywordsPlugin',
    keywords = "trac plugin ticket keywords",
    packages = ['restrictkeywords'],
    package_data={
        'restrictkeywords': [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'htdocs/images/*.gif',
        ]
    },
    entry_points = {
        'trac.plugins': [
            'restrictkeywords = restrictkeywords'
        ],
    }
)
