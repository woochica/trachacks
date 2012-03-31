#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version='0.2'

setup(
    name='EpochField',
    version=version,
    license='Modified BSD, except jquery.datetimeentry.js, jquery.datetimeentry.css, spinnerDefault.png',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='provides epoch (unix time) fields, that is time zone sensitive',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    package_data={ 'epochfield': ['htdocs/*/*'] },
    entry_points={
        'trac.plugins': [
            'EpochField.filter = epochfield.filter',
        ]
    },
)