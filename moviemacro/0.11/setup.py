#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

description = '''\
Embeds various online videos into wiki pages.
Currently supports local files and YouTube, GoogleVideo and MetaCafe movies.

This plugin makes use of the FlowPlayer [1] flash video player.
If you are in a country where bandwidth comes at a premium considder
downloading [2] the content and placing it in you htdocs directory,
then reference it as htdocs://site/filename.flv

[1] http://flowplayer.org/
[2] http://www.arrakis.es/~rggi3/youtube-dl/
'''

setup(
    name = 'MovieMacro',
    version = '0.2',
    packages = ['movie'],
    package_data = {'movie': ['htdocs/img/*.jpg',
                              'htdocs/js/*.js',
                              'htdocs/swf/*.swf']},
    author = 'Louis Cordier',
    author_email = 'lcordier@gmail.com',
    description = description,
    url = 'http://trac-hacks.org/wiki/MovieMacro/',
    license = 'BSD',
    keywords = 'trac plugin movie macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': [
        'movie.macro = movie.macro',
        'movie.web_ui = movie.web_ui'
        ]
    },
)
