#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracMultiProjectQuery',
    version = '1.0.0',
    packages = ['multiprojectquery'],

    author = "David Abrahams",
    author_email = "dave@boost-consulting.com",
    description = "Post-processes the results of cross-project queries to fix up ticket links.",
    license = "Boost Software License 1.0",
    keywords = "trac plugin ticket query 0.11 bewst report-plugin multi-projects",
    url = "http://trac-hacks.org/wiki/MultipleProjectQueryFilterPlugin",
    classifiers = [
        'Framework :: Trac',
    ],

    entry_points = {
        'trac.plugins': [
            'multiprojectquery.filter = multiprojectquery.filter',
        ]
    }
)
