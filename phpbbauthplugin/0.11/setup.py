#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'PhpBBAuth',
    version = '0.1',
    author = 'John Hampton',
    author_email = 'pacoapblo@pacopablo.com',
    url = 'http://trac-hacks.org/wiki/PhpBbAuthPlugin',
    description = 'Authentication against PhpBB3.  Requires Account Manager',

    license = 'MIT'
    zip_safe=True,
    packages=['phpbbauth'],
    install_requires = [
        'TracAccountManager>=0.2dev',
    ],

    entry_points = {
        'trac.plugins': [
            'phpbbauth.main = main.main',
        ]
    },

)
