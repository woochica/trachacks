#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License:
#   "THE BEER-WARE LICENSE" (Revision 42):
# <trac@matt-good.net> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.   Matthew Good

from setuptools import setup

setup(
    name = 'TracAccountManager',
    version = '0.1.3',
    author = 'Matthew Good',
    author_email = 'trac@matt-good.net',
    url = 'http://trac-hacks.org/wiki/AccountManagerPlugin',
    description = 'User account management plugin for Trac',

    license = 'THE BEER-WARE LICENSE',

    zip_safe=True,
    packages=['acct_mgr'],
    package_data={'acct_mgr': ['templates/*.cs']},

    install_requires = [
        'TracWebAdmin',
    ],

    entry_points = {
        'trac.plugins': [
            'acct_mgr.web_ui = acct_mgr.web_ui',
            'acct_mgr.htfile = acct_mgr.htfile',
            'acct_mgr.http = acct_mgr.http',
            'acct_mgr.api = acct_mgr.api',
            'acct_mgr.admin = acct_mgr.admin',
            'acct_mgr.db = acct_mgr.db',
            'acct_mgr.pwhash = acct_mgr.pwhash',
        ]
    },

    test_suite = 'acct_mgr.tests.suite',
)
