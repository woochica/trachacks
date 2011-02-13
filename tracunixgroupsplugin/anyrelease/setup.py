#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup, find_packages

PACKAGE = 'TracUnixGroups'
VERSION = '0.11'

setup(
    name = PACKAGE,
    version = VERSION,

    packages = find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data = True,

    author = "Vadim Zaliva",
    author_email = "lord@crocodile.org",
    description = "TracUnixGroups - use system group membership in trac.",
    long_description = "The TracUnixGroups plugin allows Trac to use the" \
        " OS group membership for permissions assignment.",
    license = "BSD",
    keywords = "trac group permission plugin",
    url = "http://trac-hacks.org/wiki/TracUnixGroupsPlugin",

    entry_points = {
        'trac.plugins': [
            '%s = %s' % (PACKAGE, 'unixgroups')
        ],
    },

    zip_safe = True
)
