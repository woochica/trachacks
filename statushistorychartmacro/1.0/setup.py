#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = '0.1'

setup(
    name='StatusHistoryChart',
    version=version,
    license='Modified BSD, except for including jquery.flot library',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='Draw chart of ticket\'s status change history. ',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    package_data={'statushistorychart': ['htdocs/*/*.js', 'htdocs/*/*/*']},
    entry_points={
        'trac.plugins': [
            'StatusHistoryChart = statushistorychart.statushistorychart',
        ],
    },
)
