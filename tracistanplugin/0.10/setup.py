#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'TracIStan'
VERSION = '0.2'

setup(  name=PACKAGE, version=VERSION,
        author = 'John Hampton',
        author_email = 'pacopablo@asylumware.com',
        url = 'http://trac-hacks.org/wiki/TracIStanPlugin',
        description = 'Trac interface for the Stan templating language',
        license='Edgewall',

        package_dir = { 'tracistan' : 'stan' },
        packages = ['tracistan'],
        package_data = { 'tracistan' : ['templates/*.stan', ]},
        entry_points = {'trac.plugins': ['tracistan = tracistan']},
#        install_requires = ['TracTags>=0.3,<0.5', 'TracWebAdmin']
)
