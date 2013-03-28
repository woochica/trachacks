#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracCondFields',
    version='2.0',
    packages=['condfields'],
    package_data={'condfields': ['templates/*']},

    author='Noah Kantrowitz',
    author_email='noah@coderanger.net',
    description='Support for conditional fields in different ticket types.',
    license='BSD 3-Clause',
    keywords='trac plugin ticket conditional fields',
    url='http://trac-hacks.org/wiki/CondFieldsPlugin',
    classifiers=[
        'Framework :: Trac',
    ],

    install_requires=['Trac>=0.11'],
    extras_require={'customfieldadmin': 'TracCustomFieldAdmin'},

    entry_points={
        'trac.plugins': [
            'condfields.web_ui = condfields.web_ui',
            'condfields.admin = condfields.admin[customfieldadmin]',
        ]
    },
)
