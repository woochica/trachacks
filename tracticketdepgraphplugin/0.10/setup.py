#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
	name = 'TracTicketDepgraph',
	version = '0.10',
	packages = ['depgraph'],
	package_data = { 'depgraph': ['htdocs/css/*.css', 'templates/*.cs', ] },

	author = "Felix Tiede",
	author_email = "felix@eyec.de",
	description = "Provides a dependency graph for blocked tickets.",
	license = "GPLv2",
	keywords = "trac plugin ticket dependencies graph",
	url = "http://trac-hacks.org/wiki/TracTicketDepgraphPlugin",
	classifiers = [
		'Framework :: Trac',
	],

	install_requires = ['TracMasterTickets', 'graphviz' ],

	entry_points = {
		'trac.plugins': [
			'TracTicketDepgraph = depgraph',
		]
	}
)
