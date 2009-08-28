"""
$Id$
$HeadURL$

Copyright (c) 2009 Pavel Plesov <pavel.plesov@gmail.com>. All rights reserved.

Python egg setup file for the mscgen trac wiki processor.
"""


__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__docformat__ = 'restructuredtext'
__version__   = '0.1'

from setuptools import setup, find_packages

setup (
	name = 'mscgen',
	version = __version__,
	packages = find_packages(),
	package_data = { 'mscgen' : [ ], },
	entry_points = {'trac.plugins': 'mscgen = mscgen'},
	author = "Pavel Plesov",
	author_email = "pavel.plesov@gmail.com",
	keywords = "trac mscgen",
	url = "http://trac-hacks.org/wiki/MscgenPlugin",
	description = "MscGen plugin for Trac 0.11",
	long_description = """
The mscgen wiki processor is a plugin for Trac that allows the
dynamic generation of message sequence chart diagrams.""",
	license = "BSD"
)
