#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup

setup(
    name = 'TracHackergotchi',
    version = '1.1',
    packages = ['hackergotchi'],
    package_data = {'hackergotchi': ['htdocs/*.js', 'htdocs/*.css']},

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Adds user-specific icons to the Trac timeline view.',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = 'BSD',
    keywords = 'trac plugin timeline identicon hackergotchi',
    url = 'http://trac-hacks.org/wiki/HackergotchiPlugin',
    classifiers = [
        'Framework :: Trac',
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'hackergotchi.api = hackergotchi.api',
            'hackergotchi.providers = hackergotchi.providers',
            'hackergotchi.web_ui = hackergotchi.web_ui',
        ],
    },
)
