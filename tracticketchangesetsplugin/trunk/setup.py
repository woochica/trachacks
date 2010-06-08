#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup, find_packages

setup(
    name = 'TracTicketChangesets',
    version = '1.0',
    author = 'Mikael Relbe',
    author_email = 'mikael@relbe.se',
    url = 'http://trac-hacks.org/wiki/TracTicketChangesetsPlugin',
    packages = find_packages(exclude=['*.tests']),
    description = 'Update referenced tickets based on commit messages.',
    long_description = open(os.path.join(os.path.dirname(__file__),
                                         'README')).read(),
    keywords = 'trac plugin ticket commit message changesets',
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    
    install_requires = ['Trac'],
    
    entry_points = """
        [trac.plugins]
        ticketchangesets.admin = ticketchangesets.admin
        ticketchangesets.init = ticketchangesets.init
        ticketchangesets.commit_updater = ticketchangesets.commit_updater
        ticketchangesets.web_ui = ticketchangesets.web_ui
    """,
)
