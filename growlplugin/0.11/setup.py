#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Emmanuel Blot <emmanuel.blot@free.fr>
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

PACKAGE = 'TracGrowlPlugin'
VERSION = '0.2.0'

setup (
    name = PACKAGE,
    version = VERSION,
    description = 'Growl Notifier for Trac events',
    author = 'Emmanuel Blot',
    author_email = 'emmanuel.blot@free.fr',
    license='BSD', 
    url='http://trac-hacks.org/wiki/GrowlPlugin',
    keywords = "trac growl event notifier",
    install_requires = [ 'Trac>=0.11dev', 'Trac<0.12'],
    packages = find_packages(exclude=['ez_setup']),
    package_data={
        'revtree': [
            'htdocs/css/*.css',
            'htdocs/images/*.png',
            'templates/*.html'
        ]
    },
    entry_points = {
        'trac.plugins': [
            'growl.notifier = growl.notifier',
            'growl.web_ui = growl.web_ui'
        ]
    }
)
