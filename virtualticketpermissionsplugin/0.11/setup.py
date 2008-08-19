#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup

setup(
    name = 'TracVirtualTicketPermissions',
    version = '1.0.0',
    packages = ['virtualticketpermissions'],

    author = 'Norman Rasmussen',
    author_email = 'norman@rasmussen.co.za',
    description = 'Modified ticket permissions for Trac.',
    #long_description = 'Allow users to only see tickets they are involved with.',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = 'BSD',
    keywords = 'trac plugin ticket permissions security',
    url = 'http://trac-hacks.org/wiki/VirtualTicketPermissionsPlugin',
    download_url = 'http://trac-hacks.org/svn/virtualticketpermissionsplugin/0.11#egg=TracVirtualTicketPermissions-dev',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'virtualticketpermissions.policy = virtualticketpermissions.policy',
        ],
    },
)
