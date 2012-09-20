#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

version='0.1'

setup(name='ExtendedVersionTracPlugin',
      version=version,
      description="Extend versions in trac",
      author='Malcolm Studd',
      author_email='mestudd@gmail.com',
      url='',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['*.tests']),
      include_package_data=True,
      package_data={ 'extendedversion': ['templates/*.html', 'htdocs/css/*.css'] },
      zip_safe=False,
      entry_points = """
          [trac.plugins]
          extendedversion.environment = extendedversion.environment
          extendedversion.milestone = extendedversion.milestone
          extendedversion.roadmap = extendedversion.roadmap
          extendedversion.version = extendedversion.version
      """,
      )

