#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Emmanuel Blot <emmanuel.blot@free.fr>
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

PACKAGE = 'TracAttachFilterPlugin'
VERSION = '0.1.0'

setup (
    name = PACKAGE,
    version = VERSION,
    description = 'Attachment enhancer for Trac',
    author = 'Emmanuel Blot',
    author_email = 'emmanuel.blot@free.fr',
    license='BSD', 
    url='http://trac-hacks.org/wiki/AttachFilterPlugin',
    keywords = "trac attachment notifier",
    install_requires = [ 'Trac>=0.12', 'Trac<0.13'],
    packages = find_packages(exclude=['ez_setup']),
    entry_points = {
        'trac.plugins': [
            'attachfilter.filter = attachfilter.filter',
        ]
    }
)
