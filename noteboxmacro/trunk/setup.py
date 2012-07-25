#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Bernhard Gruenewaldt <ryan.j.ollos@gmail.com>
# Copyright (C) 2011-2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name = 'NoteBox',
    version = 1.0,
    packages = ['notebox'],
    package_data = { 'notebox': ['htdocs/css/*.css', 'htdocs/*.png'] },
    author = 'Bernhard Gruenewaldt',
    author_email = 'trac@gruenewaldt.net',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryan.j.ollos@gmail.com',
    url = 'http://trac-hacks.org/wiki/NoteBoxMacro',
    description = 'Macro for rendering a notebox with an icon.',
    entry_points={'trac.plugins': ['NoteBox = notebox.macro']},
    keywords = 'trac macro notebox',
    license = 'GPLv2+',
)
