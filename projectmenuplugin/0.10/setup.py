#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracProjectMenu',
    version = '1.0',
    packages = ['projectmenu'],
    package_data = { 'projectmenu': ['htdocs/*.js'] },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Provide a menu entry to switch between projects in TRAC_ENV_PARENT_DIR-type setup.",
    license = "BSD",
    keywords = "trac plugin multiproject",
    url = "http://trac-hacks.org/wiki/ProjectMenuPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    #install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'projectmenu.web_ui = projectmenu.web_ui',
        ]
    }
)
