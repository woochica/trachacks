#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import sys

setup(
    name='FieldTooltip',
    version='0.2',
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/FieldTooltipPlugin',
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
