#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracExtendedXmlRpc',
    version = '0.1',
    author = 'Matteo Merli',
    author_email = 'matteo.merli@gmail.com',
    description = 'Addons module for XML-RPC interface',
    zip_safe = True,
    packages = ['tracrpcext'],
    entry_points = {'trac.plugins' : 'TracExtentedXmlRpc = tracrpcext'},
)

