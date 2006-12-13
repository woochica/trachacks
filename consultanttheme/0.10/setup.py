#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracConsultantTheme',
    version = '1.0',
    packages = ['consultanttheme'],
    package_data = { 'consultanttheme': ['templates/*.cs', 'htdocs/images/*.*', 'htdocs/*.*' ] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "A theme for Trac based on the G-Consultant theme from templateworld.com",
    license = "BSD",
    keywords = "trac plugin theme",
    url = "http://trac-hacks.org/wiki/ConsultantTheme",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracThemeEngine'],

    entry_points = {
        'trac.plugins': [
            'consultanttheme.theme = consultanttheme.theme',
        ]
    }
)
