#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'CKEditorPlugin',
    version = '0.1',
    description = 'Trac wiki WYSIWYG editor based on CKEditor',
    author = 'Edan Maor',
    author_email = 'edanm@btlms.com',
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'ckeditortrac' : [ 'htdocs/*.js', 'htdocs/*.css', 'htdocs/*.png'],

    },
    entry_points = {
        'trac.plugins': [
            'ckeditortrac = ckeditortrac',
        ],
    }
)
