#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
	name = 'TracTicketDepgraph',
	version = '0.11',
	packages = ['depgraph'],
	package_data = { 'depgraph': ['htdocs/css/*.css', 'templates/*.html', ] },

	author = "Felix Tiede",
	author_email = "felix.tiede@eyec.de",
	description = "Provides a dependency graph for blocked tickets.",
	license = "GPLv3",
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
