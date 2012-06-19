# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering
#
from setuptools import setup

setup(
    name='GroupTicketFields',
    version='0.0.1',
    packages=['groupticketfields'],
    package_data={
        'groupticketfields' : [
            'htdocs/*.js',
            'htdocs/*.png',
            'htdocs/css/*.css',
        ]
    },
    author = 'thomasd',
    author_email='tdoering@baumer.com',
    description='Group Ticket Fields',
    long_description='Group Ticket Fields',
    keywords='Group Ticket Fields',
    entry_points = {'trac.plugins': ['groupticketfields = groupticketfields']}
)