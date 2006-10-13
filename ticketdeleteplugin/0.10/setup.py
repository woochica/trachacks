#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracTicketDelete',
    version = '1.1.2',
    packages = ['ticketdelete'],
    package_data = { 'ticketdelete': ['templates/*.cs', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Remove tickets and ticket changes from Trac.",
    long_description = "Provides a web interface to removing whole tickets and ticket changes in Trac.",
    license = "BSD",
    keywords = "trac plugin ticket delete",
    url = "http://trac-hacks.org/wiki/TicketDeletePlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'ticketdelete.web_ui = ticketdelete.web_ui'
        ]
    }
)
