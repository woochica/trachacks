#!/usr/bin/env python
# -*- coding: utf-8 -*-
#### AUTHORS ####
## Primary Author:
## Colin Guthrie
## http://colin.guthr.ie/
## trac@colin.guthr.ie
## trac-hacks user: coling

from setuptools import find_packages, setup

setup(
    name='worklog',
    description='Plugin to manage the which tickets users are currently working on',
    keywords='trac plugin ticket working',
    version='0.3',
    url='http://trac-hacks.org/wiki/WorklogPlugin',
    license='http://www.opensource.org/licenses/mit-license.php',
    author='Colin Guthrie',
    author_email='trac@colin.guthr.ie',
    long_description="""
    I'll write this later!
    """,
    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'worklog': [
            'htdocs/*.css',
            'htdocs/*.js',
            'htdocs/*.png',
            'templates/*.html'
        ]
    },
    entry_points={
        'trac.plugins': [
            'worklog.admin = worklog.admin',
            'worklog.api = worklog.api',
            'worklog.ticket_daemon = worklog.ticket_daemon',
            'worklog.ticket_filter = worklog.ticket_filter',
            'worklog.timeline = worklog.timeline',
            'worklog.xmlrpc = worklog.xmlrpc[xmlrpc]',
            'worklog.webui = worklog.webui'
        ]
    },
    extras_require = {'xmlrpc': 'TracXMLRPC >= 1.1'}
)
