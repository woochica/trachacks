#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup

setup(
    name = 'TracRssEmbed',
    version = '0.0.1',
    packages = ['rssembed'],
    package_data = { 'rssembed' : ['templates/*.html', 'htdocs/css/*.css'] },
    author = 'Simon Smithson',
    author_email = 'smithsos@minchnims.net',
    description = 'A Trac macro to embed a rss feed into a wiki page, useful for the output from another trac instance.',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = 'BSD',
    keywords = 'trac plugin macro ',
    url = 'http://minchnims.net/wiki/RssEmbedMacro',
    classifiers = [
        'Framework :: Trac',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'rssembed.macro = rssembed.macro',
        ],
    },

)
