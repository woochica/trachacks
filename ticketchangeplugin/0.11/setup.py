#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracTicketChange',
    version = '0.0.4',
    packages = ['ticketchange'],
    package_data = { 'ticketchange': ['templates/*.html'] },

    author = "Sergei Luchko",
    author_email = "luchko@mail.ru",
    description = "Change ticket comments in Trac.",
    long_description = "Provides a web interface to change ticket comments in Trac.",
    license = "BSD",
    keywords = "trac plugin ticket comment change",
    url = "http://trac-hacks.org/wiki/TicketChangePlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracTicketDelete'],

    entry_points = {
        'trac.plugins': [
            'ticketchange.web_ui = ticketchange.web_ui'
        ]
    }
)
