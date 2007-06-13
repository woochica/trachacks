#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracChangesetFeedFilter',
    version = '0.1',
    author = 'Matthew Good',
    author_email = 'trac@matt-good.net',
    #url = '',
    description = 'Create filters for creating RSS feeds of changesets on select paths.',

    license = '''
"THE BEER-WARE LICENSE" (Revision 42):
<trac@matt-good.net> wrote this file.  As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return.   Matthew Good''',

    zip_safe=True,
    packages=['changesetfeedfilter'],
    #package_data={'changesetfeedfilter': ['templates/*.cs']},

    entry_points = {
        'trac.plugins': [
            'changesetfeedfilter.macros = changesetfeedfilter.macros',
            'changesetfeedfilter.web_ui = changesetfeedfilter.web_ui',
        ]
    },
    test_suite = 'changesetfeed.tests.suite',
)
