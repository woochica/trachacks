#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='Snapshot',
    version='0.1',
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='store query result to wiki as static snapshot',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    include_package_data=True,
#    package_data={ 'snapshot': [
#                      'templates/*.html',
#                      'htdocs/*/*'] },
    entry_points={
        'trac.plugins': [
            'snapshot.query = snapshot.query',
            'snapshot.macro = snapshot.macro'
        ]
    },
)
