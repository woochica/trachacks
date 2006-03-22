#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'AuthForm',
    version = '0.1',
    packages = ['authform'],
    package_data = { 'authform': ['templates/*.cs' ] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Implements form-based login against HTTP authentication",
    license = "BSD",
    keywords = "trac authentication form",
    url = "http://trac-hacks.org/",

    entry_points = {
        'trac.plugins': [
            'authform.web_ui = authform.web_ui'
        ]
    }
)
