#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracSecureTickets',
    version = '0.1.2',
    packages = ['securetickets'],
    author = 'Rob Guttman',
    author_email = 'guttman@alum.mit.edu',
    description = 'Adds ticket security policy based on component.',
    license = 'BSD',
    keywords = 'trac plugin secure tickets permissions',
    url = 'http://trac-hacks.org/wiki/SecureTicketsPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = [],

    entry_points = {
        'trac.plugins': [
            'securetickets.api = securetickets.api',
        ]
    },
)
