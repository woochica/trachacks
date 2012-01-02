#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

PACKAGE = 'TracQueues'
VERSION = '0.1.0'

setup(
    name=PACKAGE, version=VERSION,
    description='Manages ticket queues via drag-and-drop',
    author="Rob Guttman", author_email="guttman@alum.mit.edu",
    license='GPL', url='http://trac-hacks.org/wiki/TracQueuesPlugin',
    packages = ['queues'],
    package_data = {'queues':['templates/*.html','htdocs/*.css','htdocs/*.js']},
    entry_points = {'trac.plugins':['queues.web_ui = queues.web_ui']}
)
