#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracFakeUsername',
    version = '1.0',
    packages = ['fakeusername'],
    package_data = { 'fakeusername': ['htdocs/*.js'] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Report tickets using a different name than that of the logged in user.",
    license = "BSD",
    keywords = "trac plugin ticket",
    url = "http://trac-hacks.org/wiki/FakeUsernamePlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    #install_requires = [''],

    entry_points = {
        'trac.plugins': [
            'fakeusername.filter = fakeusername.filter',
        ]
    }
)
