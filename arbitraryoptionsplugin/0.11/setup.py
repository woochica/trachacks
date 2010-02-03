#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='TracArbitraryOptionsPlugin',
    version='1.0',
    packages=find_packages(),
    author='David Isaacson',
    author_email='david@icapsid.net',
    description='Allows arbitrary options to be added to Trac configuration files and accessed via the templates.  Allows data from all projects to be accessed in each.',
    url='http://trac-hacks.org/wiki/ArbitraryOptionsPlugin',
    license='Modified BSD',
    entry_points = {
        'trac.plugins': [
        	'plugin = tracarbitraryoptions'
        ]
    }
)
