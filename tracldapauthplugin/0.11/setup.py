#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracLDAPAuth',
    version = '1.0',
    packages = ['ldapauth'],

    author = 'Noah Kantrowitz',
    author_email = 'coderanger@yahoo.com',
    description = 'An AccountManager password store that uses python-ldap to check against an LDAP server.',
    license = 'BSD',
    keywords = 'trac plugin accountmanager',
    url = 'http://trac-hacks.org/wiki/LDAPAuthPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracAccountManager'],

    entry_points = {
        'trac.plugins': [
            'ldapauth.store = ldapauth.store',
        ],
    },
)
