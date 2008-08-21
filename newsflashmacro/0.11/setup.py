#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup

setup(
    name = 'TracNewsFlash',
    version = '1.0',
    packages = ['newsflash'],
    package_data = { 'newsflash' : [ 'htdocs/css/*.css' ] },
    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'A Trac macro to make a colored box.',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = 'BSD',
    keywords = 'trac plugin macro news flash',
    url = 'http://trac-hacks.org/wiki/NewsFlashMacro',
    classifiers = [
        'Framework :: Trac',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'newsflash.macro = newsflash.macro',
        ],
    },

)
