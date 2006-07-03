#!/usr/bin/env python
from setuptools import setup, find_packages

PACKAGE = 'OpenIDAuth'
VERSION = '0.1'

setup(
    name=PACKAGE, version=VERSION,
    description='Trac plugin for OpenID identification.',
    author="Waldemar Kornewald", author_email="wkornew@gmx.net",
    license='MIT', url='http://www.trac-hacks.org',
    packages=find_packages(exclude=['ez_setup', '*.tests*']),
    package_data={
        'openidauth': [
            'htdocs/css/*.css',
            'htdocs/img/*.png',
            'htdocs/js/*.js',
            'templates/*.cs'
        ]
    },
    entry_points = {
        'trac.plugins': [
            'openidauth.auth = openidauth.auth'
        ]
    }
)
