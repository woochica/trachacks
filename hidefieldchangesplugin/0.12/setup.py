#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='HideFieldChanges',
    version='0.1',
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='hide field changes in ticket history',
    zip_safe=False,
    packages=find_packages(exclude=['*.tests']),
    include_package_data=True,
    package_data={'hidefieldchanges': [
                      'templates/*.html',
                      'htdocs/*/*']},
    entry_points={
        'trac.plugins': 'HideFieldChanges = hidefieldchanges.ticket'
        },
    )
