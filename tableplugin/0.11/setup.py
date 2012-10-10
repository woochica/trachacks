#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

PACKAGE = 'TablePlugin'
VERSION = 0.1

setup(name=PACKAGE,
      version=VERSION,
      packages=['table'],
      entry_points = """
      [trac.plugins]
      table = table
      """,
)
