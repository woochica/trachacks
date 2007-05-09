#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

PACKAGE = 'TracSearchAttachmentsPlugin'
VERSION = '0.1'

setup(	name=PACKAGE,
      	author='Yannick Deltroo',
	author_email='deltroo@gmail.com',
	license='BSD',
	url='http://trac-hacks.org/wiki/SearchAttachmentsPlugin',
	version=VERSION,
	description='Text integral search in trac attachments',
	long_description="""This trac plugin uses external tools to index and search attachments""",
	packages=['searchattachments'],
	entry_points={'trac.plugins': '%s = searchattachments' % PACKAGE},
)

