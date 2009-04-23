#!/usr/bin/env python

from setuptools import setup

setup(
    name='GridFlow',
    version='0.11.2',
    description='Invoke workflows directly from report and query results',
    author='David Champion',
    author_email='dgc@uchicago.edu',
    license='COPYING',
    url='http://trac-hacks.org/wiki/GridFlowPlugin',
    packages = ['gridflow'],
    package_data = {
        'gridflow': [ 'htdocs/*.js' ]
    },
    entry_points = {
        'trac.plugins': [ 'gridflow = gridflow.gridflow', ]
    }
)
