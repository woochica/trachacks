#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

version='0.3'

setup(
	name='TracPermissionFilter',
	version=version,
	description="Filter Trac Permissions using a blacklist and/or a whitelist",
	author='Sergio Talens-Oliag',
	author_email='sto@iti.es',
	url='http://trac-hacks.org/wiki/TracPermissionFilterPlugin',
	keywords='trac plugin',
	license="GPLv3",
	packages=find_packages(
		exclude=['ez_setup', 'examples', 'tests*']
	),
	include_package_data=True,
	package_data={
		'tracpermissionfilter': ['templates/*', 'htdocs/*']
	},
	zip_safe=False,
	entry_points = {
		'trac.plugins': ['tracpermissionfilter = tracpermissionfilter']
	},
)
