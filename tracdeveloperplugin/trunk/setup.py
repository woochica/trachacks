#!/usr/bin/env python

from setuptools import setup

setup(
    name='TracDeveloper',
    version='0.2',
    packages=['tracdeveloper'],
    author='Alec Thomas',
    description='Adds some features to Trac that are useful for developers',
    url='http://trac-hacks.org/wiki/TracDeveloperPlugin',
    license='BSD',
    entry_points = {
        'trac.plugins': [
            'developer = tracdeveloper',
            'developer.debugger = tracdeveloper.debugger',
            'developer.plugins = tracdeveloper.plugins'
        ]
    },
    package_data = {
        'tracdeveloper' : [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'templates/*.html',
        ]
    }
)
