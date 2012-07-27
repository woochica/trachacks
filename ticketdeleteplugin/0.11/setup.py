#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TracTicketDelete',
    version = '3.0.0',
    packages = ['ticketdelete'],
    package_data = { 'ticketdelete': ['templates/*.html', 'htdocs/*.css' ] },
    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    maintainer= "Ryan J Ollos",
    maintainer_email = "ryan.j.ollos@gmail.com",
    description = "Remove tickets and ticket changes from Trac.",
    long_description = "Provides a web interface to removing whole tickets and ticket changes in Trac.",
    license = "BSD",
    keywords = "trac plugin ticket delete",
    url = "http://trac-hacks.org/wiki/TicketDeletePlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    entry_points = {
        'trac.plugins': [
            'ticketdelete = ticketdelete.web_ui'
        ]
    }
)
