#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'TracFileList'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['filelist'],
      package_dir={'filelist': 'filelist'},
      package_data={'filelist':['htdocs/js/*.js']},
      entry_points={'trac.plugins': '%s = filelist' % PACKAGE},
)

