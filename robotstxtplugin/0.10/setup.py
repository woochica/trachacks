#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracRobotsTxt',
    version = '1.0.1',
    packages = ['robotstxt'],
    package_data = { 'robotstxt': ['templates/*.cs' ] },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Serve a robots.txt file from Trac.",
    long_description = "Allows simple management of a robots.txt file from within Trac.",
    license = "BSD",
    keywords = "trac plugin robots",
    url = "http://trac-hacks.org/wiki/RobotsTxtPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    #install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'robotstxt.web_ui = robotstxt.web_ui'
        ]
    }
)
