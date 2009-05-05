#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup, find_packages

PACKAGE = 'TracSysgroups'
VERSION = '0.11'

setup(
    name = PACKAGE,
    version = VERSION,

    packages = find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data = True,

    author = "Peter Dulovits",
    author_email = "justice@muenchen.org",
    description = "TracSysgroups plugin to make use of Unix/Linux system groups",
    long_description = "The TracSysgroups plugin allows Trac to use the" \
        " same group definitions as used by the underlying unix/linux operating system." \
        " Groups available in your operating system than" \
        " can be used for permissions assignment in trac.",
    license = "gnu gpl v3",
    keywords = "trac group permission plugin",
    #url = "http://www.froosh.net/projects/htgroups/",

    entry_points = {
        'trac.plugins': [
            '%s = %s' % (PACKAGE, 'sysgroups')
        ],
    },

    zip_safe = True
)
