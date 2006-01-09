#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'SecureSession'
VERSION = '0.1'

setup(name=PACKAGE, version=VERSION,
      packages=find_packages(exclude=['ez_setup', '*.tests*']),)
#      package_data={'sec': ['htdocs/css/*.css', 'htdocs/img/*.png',
#                                 'htdocs/js/*.js', 'templates/*.cs']})
