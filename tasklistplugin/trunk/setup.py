#!/usr/bin/env python

from setuptools import setup

setup(
    name='TaskList',
    version='0.1',
    packages=['tasklist'],
    author='John Hampton',
    description='Provides a task list based on tickets.  Allows for very simple ticket creation',
    url='http://trac-hacks.org/wiki/TaskListPLugin',
    license='BSD',
    entry_points = {
        'trac.plugins': [
            'tasklist = tasklist.main',
        ]
    },
    package_data = {
        'tasklist' : [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'templates/*.html',
        ]
    }
)
