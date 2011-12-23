#!/usr/bin/env python
from setuptools import setup, find_packages
import sys

setup(
    name='FieldTooltip',
    version='0.1',
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/FieldTooltip',
    description='tooltip help for ticket fields',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    #package_data={
    #    'fieldtooltip': ['templates/*.html', 'htdocs/*.js', 'htdocs/*.css']
    #    },
    entry_points={
        'trac.plugins': 'FieldTooltip = fieldtooltip'
        },
    )
