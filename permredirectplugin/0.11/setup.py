#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracPermRedirect',
    version = '2.0',
    packages = ['permredirect'],

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Redirect users to the login screen on PermissionError.',
    license = 'BSD',
    keywords = 'trac plugin',
    url = 'http://trac-hacks.org/wiki/PermRedirectPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'permredirect.filter = permredirect.filter',
        ]
    },
)

