#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracSimpleTicket',
    version = '4.0b1',
    packages = ['simpleticket'],
    author = 'Noah Kantrowitz',
    author_email = 'noah+tracplugins@coderanger.net',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryan.j.ollos@gmail.com',
    description = 'Restricted ticket entry form for Trac',
    long_description = 'A Trac plugin that provides a configurable ticket entry form, with selected fields hidden from the user.',
    license = 'BSD',
    keywords = 'trac plugin restricted ticket',
    url = 'http://trac-hacks.org/wiki/SimpleTicketPlugin',
    classifiers = [
        'Framework :: Trac',
    ],    
    install_requires = ['Trac'],    
    entry_points = {
        'trac.plugins': [
            'simpleticket.web_ui = simpleticket.web_ui',
        ],
    }
)
