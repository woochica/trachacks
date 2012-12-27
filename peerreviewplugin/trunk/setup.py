#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2005-2006 Team5
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

setup(
    name='TracCodeReview',
    version='2.2',
    author="Team5",
    author_email="UNKNOWN",
    maintainer="Olemis Lang",
    maintainer_email="olemis+trac@gmail.com",
    description="Framework for code review in Trac.",
    license="3-Clause BSD",
    keywords="trac plugin code peer review",
    url="http://trac-hacks.org/wiki/PeerReviewPlugin",
    packages=find_packages(exclude=['*.tests']),
    package_data={'codereview': ['templates/*.html',
                                 'htdocs/images/*.png',
                                 'htdocs/images/*.gif',
                                 'htdocs/js/*.js']},
    entry_points={
        'trac.plugins': [
            'codereview = codereview',
        ],
    },
)
