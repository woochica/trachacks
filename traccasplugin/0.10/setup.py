#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracCAS',
    version = '1.0',
    packages = ['traccas'],

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "A modified authentication plugin to use the Yale CAS system.",
    license = "BSD",
    keywords = "trac cas authentication plugin",
    url = "http://trac-hacks.org/wiki/TracCASPlugin",

    entry_points = {
        'trac.plugins': [
            'traccas.traccas = traccas.traccas'
        ]
    }
)
