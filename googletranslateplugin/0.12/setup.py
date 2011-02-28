#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup

setup(
    name = 'TracTranslate',
    version = '0.01',
    packages = ['translate'],
    package_data = {'translate': ['htdocs/*.js', 'htdocs/*.css', 'locale/*/LC_MESSAGES/*.mo']},

    author = 'Denis Yeldandi',
    author_email = 'denis@gramant.ru',
    description = 'Adds a translate to english button to comments and ticket description',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = 'BSD',
    keywords = 'trac plugin translate',
    url = 'http://trac-hacks.org/',
    classifiers = [
        'Framework :: Trac',
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    
    install_requires = ['Trac >= 0.12'],

    entry_points = {
        'trac.plugins': [
            'translate.web_ui = translate.web_ui',
        ],
    },
)
