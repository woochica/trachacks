#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from setuptools import setup, find_packages

PACKAGE = 'TracDbAuth'
VERSION = '0.4'

setup(
    name=PACKAGE, version=VERSION,
    description='Trac DB auth plugin',
    author="Waldemar Kornewald", author_email="wkornewald@gmx.net",
    license='BSD', url='http://haiku-os.org',
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
            'dbauth.auth = dbauth.auth'
        ]
    }
)
