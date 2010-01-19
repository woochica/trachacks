#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'WikiCreoleRendererPlugin'
VERSION = '0.1'

setup(  name=PACKAGE, version=VERSION,
        author = "David Fraser",
        author_email = 'davidf@sjsoft.com',
	url = 'http://trac-hacks.org/wiki/WikiCreoleRendererPlugin',
        description = 'Renders wiki creole pages to html',
        license='BSD',
	packages=['traccreole'],
        entry_points = """
	[trac.plugins]
	traccreole.traccreole = traccreole.traccreole
	""",
        install_requires = ['Creoleparser']
)

