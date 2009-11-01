#!/usr/bin/env python

from setuptools import find_packages, setup

PACKAGE = 'TracFreeDoc'
VERSION = '0.1'

setup(
    name=PACKAGE, version=VERSION,
    author = 'Rick van der Zwet',
    author_email = 'info@rickvanderzwet.nl',
    url = 'https://trac-hacks.org/wiki/FreeDocPlugin',
    description = 'Wiki like FreeBSD Handbook plugin for Trac',

    license = 'BSDLike - http://rickvanderzwet.nl/license',

    zip_safe=True,

    packages=['freedoc'],
    package_data={'freedoc': ['htdocs/css/*.css']},

    install_requires = [
        '#trac=>0.11',
    ],

    entry_points={'trac.plugins': '%s = freedoc' % PACKAGE},
)

