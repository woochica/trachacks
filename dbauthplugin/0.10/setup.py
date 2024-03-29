#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from setuptools import setup, find_packages

PACKAGE = 'TracDbAuth'
VERSION = '0.2'

setup(
    name=PACKAGE, version=VERSION,
    description='Trac plugin for authn/authz via database',
    author="Brad Anderson", author_email="brad@dsource.org",
    license='BSD', url='http://www.dsource.org',
    packages=find_packages(exclude=['ez_setup', '*.tests*']),
    package_data={
        'dbauth': [
            'htdocs/css/*.css',
            'htdocs/img/*.png',
            'htdocs/js/*.js',
            'templates/*.cs'
        ]
    },
    entry_points = {
        'trac.plugins': [
            'dbauth.auth = dbauth.auth',
            'dbauth.perm = dbauth.perm',
            'dbauth.userdir = dbauth.userdir'
        ]
    }
)
