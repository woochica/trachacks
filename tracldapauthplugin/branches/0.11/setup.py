#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import sys

try:
    import ldap
except ImportError:
    print """The python-ldap package isn't installed on your system
(`import ldap` failed).  I would just put this in `install_requires`, but
I *do* have python-ldap on my system and I get this:

{{{
Processing dependencies for TracLDAPAuth==1.0
Searching for python-ldap==2.3.1
Reading http://pypi.python.org/simple/python-ldap/
Reading http://python-ldap.sourceforge.net/
Reading http://sourceforge.net/project/showfiles.php?group_id=2072&package_id=2011
No local packages or download links found for python-ldap==2.3.1
error: Could not find suitable distribution for Requirement.parse('python-ldap==2.3.1')
}}}

Well, that's awful.  If you know how to fix this, please file a ticket at
http://trac-hacks.org/newticket?component=TracLdapAuthPlugin&owner=k0s
"""
    sys.exit(1)

from setuptools import setup

setup(
    name = 'TracLDAPAuth',
    version = '1.0',
    packages = ['ldapauth'],

    author = 'Noah Kantrowitz',
    author_email = 'coderanger@yahoo.com',
    maintainer = 'Nikolaos Papagrigoriou',
    maintainer_email = 'nikolaos@papagrigoriou.com',
    description = 'An AccountManager password store that uses python-ldap to check against an LDAP server.',
    license = 'BSD',
    keywords = 'trac plugin accountmanager',
    url = 'http://trac-hacks.org/wiki/LDAPAuthPlugin',
    classifiers = [
        'Framework :: Trac',
    ],

    install_requires = ['TracAccountManager' ],

    entry_points = {
        'trac.plugins': [
            'ldapauth.store = ldapauth.store',
        ],
    },
)
