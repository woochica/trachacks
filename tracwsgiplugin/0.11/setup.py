#!/usr/bin/env python
from setuptools import setup, find_packages

PACKAGE = 'WSGITrac'
VERSION = '0.1'

setup(
    name=PACKAGE, version=VERSION,
    description='Trac WSGI plugin',
    author="Martin Paljak", author_email="martin@paljak.pri.ee",
    license='GPL', url='http://ideelabor.ee/opensource/',
    packages=find_packages(exclude=['ez_setup', '*.tests*']),
    entry_points = {
        'trac.plugins': [
            'wsgiplugin.wsgiplugin = wsgiplugin.wsgiplugin'
        ]
    }
)
