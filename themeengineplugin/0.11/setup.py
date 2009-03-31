#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracThemeEngine',
    version = '2.0',
    packages = ['themeengine'],
    package_data = { 'themeengine': ['templates/*.html', 'htdocs/*.js', 'htdocs/*.css', 'htdocs/img/*.gif',
                                     'htdocs/farbtastic/*.png', 'htdocs/farbtastic/*.js', 'htdocs/farbtastic/*.css' ] },

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Provide a modular interface to styling Trac.',
    license = 'BSD',
    keywords = 'trac plugin theme style',
    url = 'http://trac-hacks.org/wiki/ThemeEnginePlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac>=0.11dev-r6696'],

    entry_points = {
        'trac.plugins': [
            'themeengine.web_ui = themeengine.web_ui',
            'themeengine.api = themeengine.api',
            'themeengine.admin = themeengine.admin',
        ],
    },
)
