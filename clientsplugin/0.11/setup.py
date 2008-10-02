#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'clients'

setup(name=PACKAGE,
    description='Plugin to allow management of which ticket belong to which client',
    keywords='trac plugin ticket client',
    version='0.2',
    url='http://www.trac-hacks.org/wiki/ClientsPlugin',
    license='http://www.opensource.org/licenses/mit-license.php',
    author='Colin Guthrie',
    author_email='trac@colin.guthr.ie',
    long_description="""
    I'll write this later!
    """,
    packages=[PACKAGE],
    package_data={PACKAGE : ['templates/*.html', 'htdocs/*.css']},
    entry_points = {
        'trac.plugins': [
            'clients.api = clients.api',
            'clients.admin = clients.admin',
            'clients.client = clients.client',
            'clients.model = clients.model',
            'clients.processor = clients.processor',
            'clients.summaryinterface = clients.summaryinterface',
            'clients.milestonesummary = clients.milestonesummary',
            'clients.ticketchanges = clients.ticketchanges'
        ]
    })

#### AUTHORS ####
## Primary Author:
## Colin Guthrie
## http://colin.guthr.ie/
## trac@colin.guthr.ie
## trac-hacks user: coling
