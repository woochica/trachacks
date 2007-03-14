#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracPersonalReports',
    version = '1.0',
    packages = ['personalreports'],
    package_data = { 'personalreports': ['templates/*.cs', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = 'Noah Kantrowitz',
    author_email = 'coderanger@yahoo.com',
    description = '',
    license = 'BSD',
    keywords = 'trac plugin',
    url = 'http://trac-hacks.org/wiki/PersonalReportsPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracCtxtnavAdd'],

    entry_points = {
        'trac.plugins': [
            'personalreports.web_ui = personalreports.web_ui',
        ]
    },
)
