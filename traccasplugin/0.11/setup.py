#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracCAS',
    version = '2.0',
    packages = ['traccas'],

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'A modified authentication plugin to use the Yale CAS system.',
    license = 'BSD',
    keywords = 'trac plugin cas authentication',
    url = 'http://trac-hacks.org/wiki/TracCASPlugin',

    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'traccas.traccas = traccas.traccas'
        ]
    }
)
