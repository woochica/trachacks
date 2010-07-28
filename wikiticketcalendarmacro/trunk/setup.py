#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010, Steffen Hoffmann
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

# run a 'compile_catalog' before 'bdist_egg' (copied from Trac)
from distutils.command.build            import build
build.sub_commands.insert(0, ('compile_catalog', lambda x: True))

# 'bdist_egg' isn't that nice, all it does is an 'install_lib'
from setuptools.command.install_lib     import install_lib as _install_lib
class install_lib(_install_lib): # playing setuptools' own tricks ;-)
    def run(self):
        self.run_command('compile_catalog')
        _install_lib.run(self)
extra['cmdclass'] = {'install_lib': install_lib}

PACKAGE = "WikiTicketCalendarMacro"
VERSION = "1.2.1"

setup(
    name = PACKAGE,
    version = VERSION,
    keywords = "trac macro calendar milestone ticket",
    author = "Matthew Good",
    author_email = "trac@matt-good.net",
    maintainer = "Ryan Ollos",
    maintainer_email = "ryano@physiosonics.com",
    url = "http://trac-hacks.org/wiki/WikiTicketCalendarMacro",
    classifiers = ['Framework :: Trac'],
    description = "Full page Milestone and Ticket calendar for Trac wiki.",
    long_description = """
Display Milestones and Tickets in a calendar view, the days link to:
 - milestones (day in bold) if there is one on that day
 - a wiki page that has wiki_page_format (if exist)
 - create that wiki page, if it does not exist and
use page template (if exist) for that new page
""",
    license = """
        Copyright (c), 2010.
        Released under the 3-clause BSD license after initially being under
        THE BEER-WARE LICENSE, Copyright (c) Matthew Good.
        See changelog in source for contributors.
        """,
    install_requires = [
        'Babel>= 0.9.5',
        'Trac >= 0.12dev',
        ],

    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'wikiticketcalendar': [
            'htdocs/css/*.css',
            'locale/*/LC_MESSAGES/*.mo',
        ],
    },
    zip_safe = True,
    entry_points = {
        'trac.plugins': [
            'wikiticketcalendar = wikiticketcalendar.macro',
        ],
    },
    **extra
)
