# -*- coding: utf-8 -*-

from setuptools import setup

PACKAGE = 'DjangoIntegration'
VERSION = '1.0'

setup(name=PACKAGE,
      version=VERSION,
      packages=['djangointegration'],
      entry_points = """
	[trac.plugins]
	djangointegration = djangointegration.auth
      """
)

