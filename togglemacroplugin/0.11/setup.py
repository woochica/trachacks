#!/usr/bin/env python

from setuptools import setup

description = ''' ... '''

setup(
    name = 'ToggleMacro',
    version = '0.1',
    packages = ['toggle'],
    package_data = {'toggle': ['htdocs/js/*.js', 'htdocs/css/*.css']},
    author = 'Alexey Gelyadov',
    description = description,
    url = 'http://trac-hacks.org/wiki/ToggleMacroPlugin/',
    license = 'BSD',
    keywords = 'trac plugin toggle block macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['toggle.toggle = toggle.toggle']}
)
