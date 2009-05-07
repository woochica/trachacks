#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'LdapPlugin'
VERSION = '0.5.1'

setup (
    name = PACKAGE,
    version = VERSION,
    description = 'LDAP extensions for Trac 0.10',
    author = 'Emmanuel Blot',
    author_email = 'emmanuel.blot@free.fr',
    license='BSD', 
    url='http://trac-hacks.org/wiki/LdapPlugin',
    keywords = "trac ldap permission group acl",
    packages = find_packages(exclude=['ez_setup', '*.tests*']),
    package_data = { },
    entry_points = {
        'trac.plugins': [
            'ldapplugin.api = ldapplugin.api',
        ]
    }
)
