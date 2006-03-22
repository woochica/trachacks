#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'UnixGroups',
    version = '0.1',
    packages = ['unixgroups'],
    package_data = {  },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Allows permissions to be assigned based on local system groups",
    license = "BSD",
    keywords = "trac unix groups permissions",
    url = "http://trac-hacks.org/",

    entry_points = {
        'trac.plugins': [
            'unixgroups.unixgroups = unixgroups.unixgroups'
        ]
    }
)

