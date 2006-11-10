#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'SecureSession'
VERSION = '0.10'

setup(  name=PACKAGE, version=VERSION,
        author = 'John Hampton',
        author_email = 'pacopablo@asylumware.com',
        url = 'http://trac-hacks.org/wiki/SecSessionPlugin',
        description = 'Plugin enforcing https:// for authenticated sessions',
        license='BSD',

        packages = ['secsession'],
        entry_points = {'trac.plugins': ['secsession = secsession']},
)

