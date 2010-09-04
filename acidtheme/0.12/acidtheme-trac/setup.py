#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
	name = 'AcidTheme',
	version = '0.1',
	packages = [ 'acidtheme' ],
	package_data = { 'acidtheme': [ 'htdocs/*' ] },
	author = 'AcIdBuRnZ',
	author_email = 'acidburnz@xmail.net',
	description = 'Acid Theme for Trac',
	license = 'Apache2.0',
	keywords = 'trac plugin theme acid',
	url = '',
	classifiers = [
		'Framework :: Trac',
	],
	install_requires = ['Trac', 'TracThemeEngine>=2.0'],
	entry_points = {
		'trac.plugins': [
			'acidtheme.theme = acidtheme.theme',
		]
	},
)

