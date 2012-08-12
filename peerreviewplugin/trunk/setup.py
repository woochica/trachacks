#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracCodeReview',
    version = '2.0',
    packages = ['codereview'],
    package_data={ 'codereview' : [ 'templates/*.cs', 'htdocs/images/*.*', 'htdocs/js/*.js' ] },
    author = "Team5",
    author_email = "UNKNOWN",
    maintainer = "Noah Kantrowitz",
    maintainer_email = "noah@coderanger.net",
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


