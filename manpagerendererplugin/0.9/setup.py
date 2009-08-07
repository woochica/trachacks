#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'ManPageRendererPlugin'
VERSION = '0.1'

setup(  name=PACKAGE, version=VERSION,
        author = "Piers O'Hanlon",
        author_email = 'p.ohanlon@gmail.com',
        url = '',
        description = 'Renders Man pages to html',
        license='GPL',
	packages=['manpagerenderer'],
        entry_points = """
	[trac.plugins]
	manpagerenderer.manpagerenderer = manpagerenderer.manpagerenderer
	""",
        install_requires = ['']
)
