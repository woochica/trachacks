#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup

setup(
    name = 'TracCosign',
    version = '0.1.0',
    packages = ['traccosign'],

    author = 'Jiang Xin',
    author_email = 'worldhello.net@gmail.com',
    description = 'A modified authentication plugin to use the Michigan CoSign SSO system.',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = 'BSD',
    keywords = 'trac 0.12 plugin cosign authentication',
    url = 'http://trac-hacks.org/wiki/TracCosignPlugin',

    install_requires = ['Trac'],

    zip_safe = False,

    entry_points = {
        'trac.plugins': [
            'traccosign.login = traccosign.login'
            'traccosign.accountldap = traccosign.accountldap'
        ]
    }
)
