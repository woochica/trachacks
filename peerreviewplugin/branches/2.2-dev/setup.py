#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracCodeReview',
    version = '2.1-toddler',
    packages = ['codereview'],
    package_data={ 'codereview' : ['templates/*.cs',
                                   'templates/*.html',
                                   'htdocs/images/*.*',
                                   'htdocs/js/*.js' ] },
    author = "Team5",
    author_email = "UNKNOWN",
    maintainer = "Sebastian Marek",
    maintainer_email = "smarek@plus.net",
    description = "Framework for realtime code review within Trac.",
    license = "BSD",
    keywords = "trac plugin code peer review",
    url = "http://trac-hacks.org/wiki/PeerReviewPlugin",

    entry_points = {
        'trac.plugins': [
            'codereview = codereview',
        ],
    },

)
