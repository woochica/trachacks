#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import find_packages, setup
PACKAGE = 'tracdependency'

setup(
    name = 'TracDependencyPlugin', version = '0.11.1.6',
    packages=find_packages(exclude=['*.tests*']),
    author = 'Yuji OKAZAKI',
    author_email = 'u-z@users.sourceforge.jp',
    description = 'Provides support for ticket dependencies and summary tickets.',
    keywords = 'trac plugin ticket dependencies master',
    url='http://sourceforge.jp/users/u-z',
    license='BSD',
    entry_points = """
        [trac.plugins]
        tracdependency = tracdependency
    """,
    package_data= {'tracdependency': ['templates/*.html', 'htdocs/*.css', 'htdocs/*.png', 'htdocs/*.js']},
)
