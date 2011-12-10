# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

PACKAGE = 'TracAnalyze'
VERSION = '0.0.9'

setup(
    name=PACKAGE, version=VERSION,
    description='Analyzes tickets for dependency and other problems',
    author="Rob Guttman", author_email="guttman@alum.mit.edu",
    license='GPL', url='http://trac-hacks.org/wiki/TracAnalyzePlugin',
    packages = ['analyze'],
    package_data = {'analyze':['analyses/*.py','templates/*.html',
                               'htdocs/*.css','htdocs/*.js']},
    entry_points = {'trac.plugins':['analyze.web_ui = analyze.web_ui',
                                    'analyze.analysis = analyze.analysis']}
)
