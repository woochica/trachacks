#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'CodeReview',
    author = 'Joerg Viola',
    author_email = 'viola@objectcode.de',
    description = 'Trac plugin for review of changesets',
    version = '0.1',
    license='BSD',
    packages=['codereview'],
    entry_points = {
        'trac.plugins': [
            'codereview = codereview'
        ]
    }
)
