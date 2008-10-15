#!/usr/bin/env python

from setuptools import setup

description = '''\
Embeds Freemind mindmaps, see Freemind [1] for more details on mindmaps.
This plugin makes use of the visorFreeMind.swf [2] flash mindmap viewer.

[1] http://freemind.sourceforge.net/wiki/index.php/Main_Page
[2] http://freemind.sourceforge.net/wiki/index.php/Flash_browser
'''

setup(
    name = 'FreemindMacro',
    version = '0.1',
    packages = ['freemind'],
    package_data = {'freemind': ['htdocs/css/*.css',
                                 'htdocs/js/*.js',
                                 'htdocs/swf/*.swf']},
    author = 'Louis Cordier',
    author_email = 'lcordier@gmail.com',
    description = description,
    url = 'http://trac-hacks.org/wiki/FreemindMacro/',
    license = 'BSD',
    keywords = 'trac plugin Freemind mindmap macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['freemind.macro = freemind.macro']}
)
