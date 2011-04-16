#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name = 'TicketExtPlugin',
    version = '0.3.2',
    description = "Ticket extensions for Trac",
    url = "http://trac-hacks.org/wiki/TicketExtPlugin",
    author = "Takanori Suzuki",
    author_email = "takanorig@gmail.com",
    license = "New BSD",
    zip_safe=True,
    packages=find_packages(exclude=['*.tests*']),
    entry_points = {
        'trac.plugins': [
            'ticketext.template = ticketext.template',
            'ticketext.template_admin = ticketext.template_admin',
        ]
    },
    package_data={'ticketext': [ 'templates/*.html', 'htdocs/*.js', 'htdocs/*.css' ],}
)
