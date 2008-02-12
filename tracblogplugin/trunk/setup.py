#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'tBlog'
VERSION = '0.3'

setup(  name=PACKAGE, version=VERSION,
        author = 'John Hampton',
        author_email = 'pacopablo@pacopablo.com',
        url = 'http://trac-hacks.org/wiki/TracBlogPlugin',
        description = 'Bloging system plugin for Trac',
        license='BSD',

        packages = ['tBlog'],
        package_data = { 'tBlog' : ['htdocs/css/*.css', 'htdocs/img/*',
                                    'templates/*.html', ]},
        entry_points = {'trac.plugins': ['tBlog = tBlog']},
        install_requires = ['TracTags>=0.6']
)
