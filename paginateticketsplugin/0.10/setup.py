#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracPaginateTickets',
    version = '0.1',
    packages = ['paginate'],
    package_data={ 'paginate' : [ 'templates/*.cs' ] },
    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Paginate ticket views.",
    license = "BSD",
    keywords = "trac plugin paginate ticket",
    url = "http://trac-hacks.org/wiki/PaginateTicketPlugin",

    entry_points = {
        'trac.plugins': [
            'paginate.web_ui = paginate.web_ui',
        ],
    },

)
