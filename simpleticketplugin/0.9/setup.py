#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracSimpleTicket',
    version = '0.1',
    packages = ['simpleticket'],

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Restricted ticket entry form",
    license = "BSD",
    keywords = "trac plugin restricted ticket",
    url = "http://trac-hacks.org/wiki/SimpleTicketPlugin",

    entry_points = {
        'trac.plugins': [
            'simpleticket.web_ui = simpleticket.web_ui',
        ],
    }
)
