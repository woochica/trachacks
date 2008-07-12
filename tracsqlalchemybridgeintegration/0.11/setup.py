#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8


from setuptools import setup, find_packages
import tracext.sa

setup(name=tracext.sa.__package__,
      version=tracext.sa.__version__,
      author=tracext.sa.__author__,
      author_email=tracext.sa.__email__,
      url=tracext.sa.__url__,
      download_url='http://python.org/pypi/%s' % tracext.sa.__package__,
      description=tracext.sa.__summary__,
      long_description=tracext.sa.__description__,
      license=tracext.sa.__license__,
      platforms="OS Independent - Anywhere Python, Trac >=0.11 and SQLAlchemy is known to run.",
      install_requires = ['Trac>=0.11', 'SQLAlchemy'],
      keywords = "bridge sqlalchemy trac",
      packages=['tracext', 'tracext.sa'],
      namespace_packages=['tracext'],
)
