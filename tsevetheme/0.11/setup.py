#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
	name = 'TseveTheme',
	version = '1.0',
	packages = [ 'tsevetheme' ],
	package_data = { 'tsevetheme': [ 'htdocs/*.css', 'htdocs/*.png', 'templates/*.html' ] },
	author = 'Carlos Jenkins',
	author_email = 'carlos.jenkins.perez@gmail.com',
	description = 'Tseve Minimalist Theme for Trac',
	license = 'CC-BY-SA',
	keywords = 'trac plugin theme tseve',
	url = 'http://www.cjenkins.net/',
	classifiers = [
		'Framework :: Trac',
	],
	install_requires = ['Trac', 'TracThemeEngine>=2.0'],
	entry_points = {
		'trac.plugins': [
			'tsevetheme.theme = tsevetheme.theme',
		]
	},
)

