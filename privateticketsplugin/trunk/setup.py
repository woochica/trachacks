#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup

setup(
    name = 'TracPrivateTickets',
    version = '2.1.0',
    packages = ['privatetickets'],

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Modified ticket security for Trac.',
    #long_description = 'Allow users to only see tickets they are involved with.',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = 'BSD',
    keywords = 'trac plugin ticket permissions security',
    url = 'http://trac-hacks.org/wiki/PrivateTicketsPlugin',
    download_url = 'http://trac-hacks.org/svn/privateticketsplugin/0.11#egg=TracPrivateTickets-dev',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'privatetickets.policy = privatetickets.policy',
        ],
    },
)
