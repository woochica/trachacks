#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='TracLinks',
    version='0.3',
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='generate TracLinks for the page',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    package_data={ 'traclinks': ['htdocs/*/*'] },
    entry_points={
        'trac.plugins': [
            'TracLinks = traclinks.textbox',
        ]
    },
)