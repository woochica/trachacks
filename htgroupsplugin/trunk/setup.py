#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracHtgroups',
    version = '0.1',
    packages = ['htgroups'],

    author = "Robin Frousheger",
    author_email = "Robin@home.froosh.net",
    description = "TracHtGroups plugin to use Apache's group file.",
    long_description = "The TracHtgroups plugin allows Trac to use the" \
        " same group definition file as used by AuthGroupFile or" \
        " AuthDigestGroupFile directives.  Groups listed in that file" \
        " can be used for permissions assignment.",
    license = "Beerware",
    keywords = "trac group permission plugin",
    url = "http://www.froosh.net/projects/htgroups/",

    zip_safe = True
)
