#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Max Sinelnikov <siniy@unigine.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
	name='TeamCityPlugin',
	author='Max Sinelnikov',
	author_email='siniy@unigine.com',
	version='0.3',
	license='BSD 3-Clause',
	packages=find_packages(exclude=['*.tests*']),
	install_requires=[
		"lxml>=2.2",
	],
	entry_points = """
	[trac.plugins]
	teamcity.web_ui = teamcity.web_ui
	teamcity.timeline = teamcity.timeline
	teamcity.admin = teamcity.admin
	""",
	package_data={'teamcity': ['templates/*.html',
						'htdocs/css/*.css',
						'htdocs/img/*.gif',
						'htdocs/js/*.js',]},
)
