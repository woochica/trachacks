#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# BackLinks plugin for Trac
#
# Author: Trapanator trap@trapanator.com
# Website: http://www.trapanator.com/blog/archives/category/trac
# License: GPL 3.0
#

from setuptools import setup, find_packages

setup(
    name = 'BackLinksMacro',
    version = '7.0',
    author = "Trapanator",
    author_email = "trap@trapanator.com",
    description = """A wiki macro to show links to other wiki pages which link \
                     to the page the macro is called from.""",
    long_description = """A wiki macro to show links to other wiki pages which link \
                     to the page the macro is called from.""",
    license = "GPLv3",
    url = 'http://trac-hacks.org/wiki/BackLinksMacro',
    packages=find_packages(exclude=['*.tests']),
    entry_points = {
        'trac.plugins': [
            'BackLinksMacro = backlinks.macro'
        ]
    },
)
