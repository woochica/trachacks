#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'LdapPlugin'
VERSION = '0.4.4'

setup (
    name = PACKAGE,
    version = VERSION,
    packages = find_packages(exclude=['ez_setup', '*.tests*']),
    package_data = { },
    author = "Emmanuel Blot",
    author_email = "manu.blot@gmail.com",
    description = "LDAP extensions for Trac 0.10",
    keywords = "trac ldap permission group acl",
    url = "http://trac-hacks.swapoff.org/wiki/LdapPlugin",
)

