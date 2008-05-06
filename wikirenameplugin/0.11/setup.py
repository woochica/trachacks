#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup

setup(
    name = 'TracWikiRename',
    version = '2.1',
    packages = ['wikirename'],
    package_data = {'wikirename': ['templates/*.html']},

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Add simple support for renaming/moving wiki pages',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = 'BSD',
    keywords = 'trac 0.11 plugin wiki page rename',
    url = 'http://trac-hacks.org/wiki/WikiRenamePlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac'],
    
    entry_points = {
        'trac.plugins': [
            'wikirename.web_ui = wikirename.web_ui',
        ],
        'console_scripts': [
            'trac-wikirename = wikirename.script:run'
        ],
    },
)
