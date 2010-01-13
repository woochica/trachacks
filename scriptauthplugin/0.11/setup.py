#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'ScriptAuth',
    version = '0.1',
    author = 'Carsten Fuchs Software',
    author_email = 'info@cafu.de',
    url = 'http://trac-hacks.org/wiki/ScriptAuthPlugin',
    description = 'Authentication using a web script. Requires Account Manager.',

    license = 'MIT',
    zip_safe=True,
    packages=['scriptauth'],
    install_requires = [
        'TracAccountManager>=0.2dev',
    ],

    classifiers = [
        'Framework :: Trac',
    ],

    keywords="acct_mgr script",

    entry_points = {
        'trac.plugins': [
            'scriptauth.main = scriptauth.main',
        ]
    },

)
