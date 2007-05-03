#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'RemovePendingStatusPlugin',
    version = '0.0.1',
    packages = ['removepending'],

    author = "Daniel Atallah",
    author_email = "datallah@pidgin.im",
    description = "Remove 'pending' flag when the reporter responts to a ticket.",
    long_description = "A Trac plugin that will remove the 'pending' flag on a ticket (if present) when the reporter responds to it.",
    license = "BSD",
    keywords = "trac plugin pending ticket",
    url = "http://trac-hacks.org/wiki/PendingTicketPlugin",
    classifiers = [
        'Framework :: Trac',
    ],

    entry_points = {
        'trac.plugins': [
            'removepending.remove_pending = removepending.remove_pending',
        ],
    }
)
