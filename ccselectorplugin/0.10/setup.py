#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'cc_selector'

setup(name=PACKAGE,
      description='Visual cc editor for Trac',
      keywords='cc checkbox editor',
      version='0.0.2',
      author='Vladislav Naumov',
      author_email='vnaum@vnaum.com',
      packages=[PACKAGE],
      package_data={PACKAGE : ['htdocs/*', 'templates/*']},
      entry_points={'trac.plugins': 'cc_selector = cc_selector'}
      )


