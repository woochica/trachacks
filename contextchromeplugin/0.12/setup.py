#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='ContextChrome',
    version='0.2',
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='Add context-aware css attribute or style',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    #package_data={
    #    'contextchrome': ['templates/*.html', 'htdocs/*.js', 'htdocs/*.css']
    #    },
    entry_points={
        'trac.plugins': [
            'ContextChrome = contextchrome.style',
            'DecayedWiki = decayed.wiki',
            'z.LinkDecorator = contextchrome.linkdeco',
        ]
    },
)