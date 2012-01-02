#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

PACKAGE = 'TracVisualization'
VERSION = '0.0.1'

setup(
    name=PACKAGE, version=VERSION,
    description='Graphs tables and other data using Google Visualization API',
    author="Rob Guttman", author_email="guttman@alum.mit.edu",
    license='GPL', url='http://trac-hacks.org/wiki/TracVisualizationPlugin',
    packages = ['viz'],
    package_data = {'viz':['templates/*.html','htdocs/*.css','htdocs/*.js']},
    entry_points = {'trac.plugins':['viz.web_ui = viz.web_ui']}
)
