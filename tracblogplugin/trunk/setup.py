#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'TracBlogPlugin'
VERSION = '0.3'

setup(  name=PACKAGE, version=VERSION,
        author = 'John Hampton',
        author_email = 'pacopablo@pacopablo.com',
        url = 'http://trac-hacks.org/wiki/TracBlogPlugin',
        description = 'Blogging plugin for Trac',
        license='BSD',

        packages = ['tracblog'],
        package_data = { 'tracblog' : ['htdocs/css/*.css', 'htdocs/img/*',
                                    'templates/*.html', ]},
        entry_points = {'trac.plugins': ['tracblog = tracblog']},
        install_requires = ['TracTags>=0.6']
)
