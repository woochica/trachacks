#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

PACKAGE = 'TracDynamicVariables'
VERSION = '0.1.0'

setup(
    name=PACKAGE, version=VERSION,
    description='Default and convert report dynamic variables to pulldowns',
    author="Rob Guttman", author_email="guttman@alum.mit.edu",
    license='GPL', url='http://trac-hacks.org/wiki/TracQueuesPlugin',
    packages = ['dynvars'],
    package_data = {'dynvars':['templates/*.html','htdocs/*.js']},
    entry_points = {'trac.plugins':['dynvars.web_ui = dynvars.web_ui']}
)
