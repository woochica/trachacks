#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Emmanuel Blot <emmanuel.blot@free.fr>
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

PACKAGE = 'TracRevtreePlugin'
VERSION = '0.5.8'

setup (
    name = PACKAGE,
    version = VERSION,
    description = 'Revision Graph for the Version Control Browser',
    author = 'Emmanuel Blot',
    author_email = 'emmanuel.blot@free.fr',
    license='BSD', 
    url='http://trac-hacks.org/wiki/RevtreePlugin',
    keywords = "trac revision svg graphical tree browser",
    packages = find_packages(exclude=['ez_setup', '*.tests*', '*.enhancers.*']),
    package_data={
        'revtree': [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'htdocs/images/*.gif',
            'templates/*.html'
        ]
    },
    entry_points = {
        'trac.plugins': [
            'revtree.web_ui = revtree.web_ui',
            'revtree.enhancer = revtree.enhancer',
            'revtree.optimizer = revtree.optimizer'
        ]
    }
)
