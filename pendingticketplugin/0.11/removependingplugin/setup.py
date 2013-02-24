#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'RemovePendingStatusPlugin',
    version = '0.0.5',
    packages = ['removepending'],

    author = "Daniel Atallah",
    author_email = "datallah@pidgin.im",
    description = "Switch from 'pending' status to a configurable status when the reporter responds to a ticket.",
    long_description =
    """A Trac plugin that will switch the ticket status from 'pending' to the value stored in:

       [ticket]
       pending_removal_status = new

       when the reporter responds to it.
    """,
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
