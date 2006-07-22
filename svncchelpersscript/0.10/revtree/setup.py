#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.

from setuptools import setup, find_packages

PACKAGE = 'TracRevisionTree'
VERSION = '0.2.7'

setup(
    name=PACKAGE, version=VERSION,
    description='Graphical browser for Subversion revisions',
    author="Emmanuel Blot", author_email="emmanuel.blot@free.fr",
    license='BSD', url='',
    packages=find_packages(exclude=['ez_setup', '*.tests*']),
    package_data={
        'revtree': [
            'htdocs/css/*.css',
            'templates/*.cs'
        ]
    },
    entry_points = {
        'trac.plugins': [
            'revtree.web_ui = revtree.web_ui',
        ]
    }
)
