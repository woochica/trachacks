#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import sys

try:
    import ldap
except ImportError:
    print """The python-ldap package isn't installed on your system."""
    sys.exit(1)

from setuptools import setup, find_packages

setup(
    name = 'LDAPAuthNZPlugin',
    version = '1.0',
    packages = find_packages(),

    author = 'Larry Ruiz',
    author_email = 'larry.b.ruiz@gmail.com',
    description = 'An AccountManager LDAP password store implementation.',
    license = 'Apache License 2.0',
    install_requires = ['TracAccountManager'],
    entry_points = {
        'trac.plugins': [
            'tautua.trac_plugins.security.ldapauth = tautua.trac_plugins.security.ldapauth'
        ],
    },
)
