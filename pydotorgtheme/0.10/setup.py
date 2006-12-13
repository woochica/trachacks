#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracPyDotOrgTheme',
    version = '1.0',
    packages = ['pydotorgtheme'],
    package_data = { 'pydotorgtheme': ['templates/*.cs', 'htdocs/*.png'] },

    author = "Jeroen Ruigrok van der Werven",
    author_email = 'asmodai@in-nomine.org',
    maintainer = 'Noah Kantrowitz',
    maintainer_email = "coderanger@yahoo.com",
    description = "A theme for Trac based on python.org",
    license = "BSD",
    keywords = "trac plugin theme",
    url = "http://trac-hacks.org/wiki/PyDotOrgTheme",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracThemeEngine'],

    entry_points = {
        'trac.plugins': [
            'pydotorgtheme.theme = pydotorgtheme.theme',
        ]
    }
)
