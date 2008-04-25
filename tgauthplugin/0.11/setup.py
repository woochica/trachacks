#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TGAuth',
    version = '0.1',
    author = 'John Hampton',
    author_email = 'pacoapblo@pacopablo.com',
    url = 'http://trac-hacks.org/wiki/TgAuthPlugin',
    description = 'Authentication against TurboGears identity framework.  Requires Account Manager',

    license = 'BSD',
    zip_safe=True,
    packages=['tgauth'],
    install_requires = [
        'TracAccountManager>=0.2dev',
    ],

    entry_points = {
        'trac.plugins': [
            'tgauth.main = tgauth.main',
        ]
    },

)
