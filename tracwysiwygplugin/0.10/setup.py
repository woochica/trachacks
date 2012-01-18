#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'TracWysiwyg',
    version = '0.10.0.4',
    description = 'TracWiki WYSIWYG Editor',
    license = 'BSD',
    url = 'http://trac-hacks.org/wiki/TracWysiwygPlugin',
    author = 'Jun Omae',
    author_email = 'omae@opengroove.com',
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'tracwysiwyg' : [ 'htdocs/*.js', 'htdocs/*.css', 'htdocs/*.png' ],
    },
    entry_points = {
        'trac.plugins': [
            'tracwysiwyg = tracwysiwyg',
        ],
    }
)
