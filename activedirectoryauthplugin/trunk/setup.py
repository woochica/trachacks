#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>
# Extended: Branson Matheson <branson.matheson@nasa.gov>

from setuptools import setup, find_packages

PACKAGE = 'TracActiveDirectoryAuth'
VERSION = '0.4.1'

setup(  name=PACKAGE, version=VERSION,
        author = 'John Hampton',
        author_email = 'pacopablo@pacopablo.com',
        maintainer = 'Branson Matheson',
        maintainer_email = 'branson.matheson@nasa.gov',
        description = 'Trac Authentication against Active Directory ',
        url = 'http://trac-hacks.org/wiki/ActiveDirectoryAuthPlugin',
        license='BSD',
        zip_safe = True,
        packages = ['tracext', 'tracext.adauth'],
        entry_points = {
            'trac.plugins': [
                'adauth.db = tracext.adauth.db',
                'adauth = tracext.adauth',
                'adauth.permissionstore = tracext.adauth.api:UserExtensiblePermissionStore',
            ],
        },
        namespace_packages=['tracext'],
        install_requires = ['Trac >=0.11', 'TracAccountManager', 'python-ldap'],
)
