#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010,2011 Steffen Hoffmann
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the authors nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from setuptools     import find_packages, setup

extra = {}

try:
    from trac.util.dist  import  get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py',                'python', None),
        ]
        extra['message_extractors'] = {
            'wikicalendar': extractors,
        }
# i18n is implemented to be optional here
except ImportError:
    pass


PACKAGE = "WikiCalendarMacro"
VERSION = "2.0.0"

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
        Copyright (c), 2010.
        Released under the 3-clause BSD license after initially being under
        THE BEER-WARE LICENSE, Copyright (c) Matthew Good.
        See changelog in source for contributors.
        """,
    install_requires = ['Genshi >= 0.5', 'Trac >= 0.11'],
    extras_require = {'Babel': 'Babel>= 0.9.5', 'Trac': 'Trac >= 0.12'},
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'wikicalendar': ['htdocs/*', 'locale/*/LC_MESSAGES/*.mo'],
    },
    zip_safe = True,
    entry_points = {
        'trac.plugins': [
            'wikicalendar = wikicalendar.macros',
        ],
    },
    **extra
)
