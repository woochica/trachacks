#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
	name = 'DepgraphSidebar',
	version = '0.11',
	packages = ['depgraph'],
        package_data = { 'depgraph': ['templates/*.html', ] },
        
	author = "Michal Papis",
	author_email = "mpapis@niczsoft.com",
	description = "Provides a dependency graph for blocked tickets on the sidebar - right to the ticket.",
	license = "GPLv3",
	keywords = "trac plugin ticket dependencies graph on sidebar",
	url = "http://trac-hacks.org/wiki/DepgraphSidebarPlugin",
	classifiers = [
		'Framework :: Trac',
	],

	install_requires = ['TracMasterTickets','TicketSidebarProvider',],

	entry_points = {
		'trac.plugins': [
			'DepgraphSidebar = depgraph.sidebar',
		]
	}
)
