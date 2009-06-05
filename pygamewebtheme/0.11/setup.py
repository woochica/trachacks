#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup

setup(
    name = 'TracPygamewebTheme',
    version = '1.0',
    packages = ['pygamewebtheme'],
    package_data = {'pygamewebtheme': ['templates/*.html', 'htdocs/*.js', 'htdocs/*.css', 'htdocs/*.png']},
    include_package_data=True,

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = '',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = 'BSD',
    keywords = 'trac plugin',
    url = 'http://trac-hacks.org/wiki/PygamewebTheme',
    download_url = 'http://trac-hacks.org/svn/pygamewebtheme/0.11#egg=TracPygamewebTheme-dev',
    classifiers = [
        'Framework :: Trac',
        'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'pygamewebtheme.theme = pygamewebtheme.theme',
        ]
    },
)
