#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'ChangeLogMacro',
    version = '0.2',
    packages = ['changelog'],
    author = 'Alec Thomas',
    maintainer = 'Ryan Ollos',
    maintainer_email = 'rjollos@gmail.com',
    description = 'Adds a Wiki macro that displays the changelog for a repository path',
    keywords = 'trac scm macro plugin',
    url = 'http://trac-hacks.org/wiki/ChangeLogMacro',
    entry_points = {
        'trac.plugins':[
            'changelog.ChangeLogMacro = changelog.ChangeLogMacro'
        ]
    },
   install_requires = ['trac >= 0.13dev'],
)
