#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TracMessageOfTheDayPlugin',
    version = '0.1',
    packages = ['tracmotd'],
    package_data = {
      'tracmotd': [ 'htdocs/*.css', 'htdocs/*.js' ]
    },
    author = 'Christian Masopust',
    author_email = 'christian.masopust@chello.at',
    description = 'MOTD Trac Plugin',
    url = 'http://trac-hacks.org/wiki/MotdPlugin',
    license = 'GPLv3',
    zip_safe = False,
    keywords = 'trac plugin motd',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracmotd.motd = tracmotd.motd']}
)

