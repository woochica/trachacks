#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

PACKAGE = 'TracCloud'
VERSION = '0.1.0'

setup(
    name=PACKAGE, version=VERSION,
    description='Orchestrates AWS cloud resources via Chef',
    author="Rob Guttman", author_email="guttman@alum.mit.edu",
    license='GPL', url='http://trac-hacks.org/wiki/CloudPlugin',
    packages = ['cloud'],
    package_data = {'cloud':['templates/*.html','htdocs/*.js','htdocs/*.css']},
    entry_points = {'trac.plugins':['cloud.web_ui = cloud.web_ui',
                                    'cloud.handlers = cloud.handlers']}
)
