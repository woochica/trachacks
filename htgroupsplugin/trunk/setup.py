#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup, find_packages

PACKAGE = 'TracHtgroups'
VERSION = '0.11'

setup(
    name = PACKAGE,
    version = VERSION,

    packages = find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data = True,

    author = "Robin Frousheger",
    author_email = "Robin@home.froosh.net",
    description = "TracHtgroups plugin to use Apache's group file.",
    long_description = "The TracHtgroups plugin allows Trac to use the" \
        " same group definition file as used by AuthGroupFile or" \
        " AuthDigestGroupFile directives.  Groups listed in that file" \
        " can be used for permissions assignment.",
    license = "Beerware",
    keywords = "trac group permission plugin",
    url = "http://www.froosh.net/projects/htgroups/",

    entry_points = {
        'trac.plugins': [
            '%s = %s' % (PACKAGE, 'htgroups')
        ],
    },

    zip_safe = True
)
