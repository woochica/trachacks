#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TicketDelete',
    version = '0.1',
    packages = ['ticketdelete'],
    package_data = { 'ticketdelete': ['templates/*.cs' ] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "A small plugin to remove tickets from Trac.",
    license = "BSD",
    keywords = "trac ticket delete",
    url = "http://trac-hacks.org/",

)
