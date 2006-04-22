#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'aftracistan'
VERSION = '0.1'

setup(  name=PACKAGE, version=VERSION,
        author = 'John Hampton',
        author_email = 'pacopablo@asylumware.com',
        url = 'http://trac-hacks.org/wiki/TraciStanPlugin',
        description = """
Example plugin showing the use of the IStanRequestHandler
"""
        license='BSD',

        packages = ['aftracistan'],
        package_data = { 'aftracistan' : ['htdocs/css/*.css', 'htdocs/img/*',
                                    'templates/*.stan', ]},
        entry_points = {'trac.plugins': ['aftracistan = aftracistan']}
        install_requires = ['TracIStan']
)
