#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

PACKAGE = 'clients'

setup(name=PACKAGE,
    description='Plugin to allow management of which ticket belong to which client',
    keywords='trac plugin ticket client',
    version='0.5',
    url='http://www.trac-hacks.org/wiki/ClientsPlugin',
    license='http://www.opensource.org/licenses/mit-license.php',
    author='Colin Guthrie',
    author_email='trac@colin.guthr.ie',
    long_description="""
    I'll write this later!
    """,
    packages=find_packages(exclude=['*.tests']),
    package_data={PACKAGE : ['templates/*.html', 'htdocs/*.css']},
    entry_points = {
        'trac.plugins': [
            'clients.api = clients.api',
            'clients.client = clients.client',
            'clients.model = clients.model',
            'clients.admin = clients.admin',
            'clients.events = clients.events',
            'clients.eventsadmin = clients.eventsadmin',
            'clients.processor = clients.processor',
            'clients.summary = clients.summary',
            'clients.summary_milestone = clients.summary_milestone',
            'clients.summary_ticketchanges = clients.summary_ticketchanges',
            'clients.summary_monthlyhours = clients.summary_monthlyhours',
            'clients.action = clients.action',
            'clients.action_email = clients.action_email',
            'clients.action_zendesk_forum = clients.action_zendesk_forum',
        ]
    },
    test_suite='clients.tests.test_suite',
    tests_require=[]
    )

#### AUTHORS ####
## Primary Author:
## Colin Guthrie
## http://colin.guthr.ie/
## trac@colin.guthr.ie
## trac-hacks user: coling
