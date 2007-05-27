#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracModAuthAcctmgr',
    version = '0.1',
    packages = ['mod_auth_acctmgr'],
    #package_data={ 'mod_auth_acctmgr' : [ ] },
    
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "mod_python authentication handler for Trac's AccountManager",
    long_description = "Provide HTTP authentication using the AccountManager plugin through mod_python.",
    license = "BSD",
    keywords = "trac authentication mod_python",
    url = "http://trac-hacks.org/wiki/ModAuthAcctmgrScript",
    zip_safe = False,
    
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracAccountManager'],

    entry_points = {
        'trac.plugins': [
            'mod_auth_acctmgr.perms = mod_auth_acctmgr.perms',
        ]
    },
)
