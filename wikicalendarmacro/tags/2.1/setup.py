#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2013 Steffen Hoffmann
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Steffen Hoffmann

from setuptools import find_packages, setup

extra = {}

has_cmdclass = True
has_trac_extract_python = False
try:
    from trac.dist import get_l10n_cmdclass
    try:
        from trac.dist import extract_python
        has_trac_extract_python = True
    except ImportError:
        # Trac < 1.0, using compatibility code here.
        pass
except ImportError:
    # Trac < 0.12.2, next is trying the old location.
    try:
        from trac.util.dist import get_l10n_cmdclass
    except ImportError:
        # Trac < 0.12, i18n is implemented to be optional here.
        has_cmdclass = False
if has_cmdclass:
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        if has_trac_extract_python:
            extractors = [
                ('**.py', 'trac.dist:extract_python', None)
            ]
        else:
            extractors = [
                ('**.py', 'wikicalendar.compat:extract_python', None)
            ]
        extra['message_extractors'] = {
            'wikicalendar': extractors,
        }


PACKAGE = "WikiCalendarMacro"
VERSION = "2.1.0"

setup(
    name = PACKAGE,
    version = VERSION,
    author = "Matthew Good",
    author_email = "trac@matt-good.net",
    maintainer = "Steffen Hoffmann",
    maintainer_email = "hoff.st@web.de",
    url = "http://trac-hacks.org/wiki/WikiCalendarMacro",
    description = "Configurable calendars for Trac wiki.",
    long_description = """
Display Milestones and Tickets in a calendar view, the days link to:
 - milestones (day in bold) if there is one on that day
 - a wiki page that has wiki_page_format (if exist)
 - create that wiki page, if it does not exist and
use page template (if exist) for that new page.
Many different presentations are possible by using a certain macro
with one or more of it's corresponding attributes.
""",
    keywords = "trac macro calendar milestone ticket",
    classifiers = ['Framework :: Trac'],

    license = """
        Copyright (c), 2010,2011.
        Released under the 3-clause BSD license after initially being under
        THE BEER-WARE LICENSE, Copyright (c) Matthew Good.
        See changelog in source for contributors.
        """,

    install_requires = ['Trac >= 0.11'],
    extras_require = {'Babel': 'Babel>= 0.9.5', 'Trac': 'Trac >= 0.12'},
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'wikicalendar': [
            'htdocs/*', 'locale/*/LC_MESSAGES/*.mo', 'locale/.placeholder',
        ]
    },
    test_suite = 'wikicalendar.tests.suite',
    zip_safe = True,
    entry_points = {
        'trac.plugins': [
            'wikicalendar = wikicalendar.macros',
        ]
    },
    **extra
)
