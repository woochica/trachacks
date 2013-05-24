#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

PACKAGE = 'TracDynamicFields'
VERSION = '1.2.3'

setup(
    name=PACKAGE, version=VERSION,
    description='Dynamically hide, default, copy, clear,' +\
                ' validate, set ticket fields',
    author="Rob Guttman", author_email="guttman@alum.mit.edu",
    license='GPL', url='http://trac-hacks.org/wiki/DynamicFieldsPlugin',
    packages = ['dynfields'],
    package_data = {'dynfields':['templates/*.html',
                                 'htdocs/*.js','htdocs/*.css']},
    entry_points = {'trac.plugins':['dynfields.web_ui = dynfields.web_ui',
                                    'dynfields.rules = dynfields.rules']},
    test_suite='dynfields.tests.test_suite',
    tests_require=[]
)
