# This program is free software; you can redistribute and/or modify it
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from setuptools import setup

PACKAGE = 'TracCvsntPlugin'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['CvsntPlugin'],
      entry_points={'trac.plugins': 'cvsnt = CvsntPlugin.CvsntPlugin'},
)
