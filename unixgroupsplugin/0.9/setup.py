#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracUnixGroups',
    version = '0.1-r1',
    packages = ['unixgroups'],
    package_data = {  },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Use UNIX groups in Trac",
    long_description = "Allows permissions to be assigned based on local system groups",
    license = "BSD",
    keywords = "trac plugin unix groups permissions",
    url = "http://trac-hacks.org/wiki/UnixGroupsPlugin",

    entry_points = {
        'trac.plugins': [
            'unixgroups.unixgroups = unixgroups.unixgroups'
        ]
    }
)

