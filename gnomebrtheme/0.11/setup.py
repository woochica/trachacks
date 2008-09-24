#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'GnomeBRTheme',
    version = '0.1',
    packages = ['gnomebrtheme'],
    package_data = { 'gnomebrtheme': ['htdocs/*.css', 'htdocs/*.png'] },

    author = "Wilson Pinto Júnior",
    author_email = 'wilson@openlanhouse.org',
    description = "A theme for Trac based on br.gnome.org",
    keywords = "trac plugin theme",
    #url = "http://trac-hacks.org/wiki/PyDotOrgTheme",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracThemeEngine'],

    entry_points = {
        'trac.plugins': [
            'gnomebrtheme.theme = gnomebrtheme.theme',
        ]
    }
)
