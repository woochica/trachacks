#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
 Copyright (C) 2008 General de Software de Canarias.
 
 Author: Carlos López Pérez <carlos.lopezperez@gmail.com>
'''


from setuptools import setup

PACKAGE = 'AccountLDAPPlugin'
VERSION = '0.32'

setup(
    name = 'AccountLDAP',
    version = VERSION,
    author = "Carlos López Pérez",
    author_email = "carlos.lopezperez@gmail.com",
    url = "http://trac-hacks.org/wiki/AccountLDAP",
    
    description = "Integrate account trac user with properties defined in LDAP.",
    long_description = "Integrate account trac user with properties defined in LDAP.",
    
    license = "LGPL",
    keywords = "trac plugin ldap account",
    
    
    packages = ['accountldap'],
    package_data= {'accountldap': ['templates/*.html']},    

    entry_points = """
        [trac.plugins]
        %s = accountldap
    """ % PACKAGE,
)
