#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

version='0.1'

setup(name='MultiTracStatistics',
      version=version,
      description="Add statistics to a wiki page about multiple tracs.",
      author='David Francos Cuartero (XayOn)',
      author_email='dfrancos@warp.es',
      keywords='trac plugin',
      license="GPLv3+",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      Wstats.macro = Wstats.macro
      """,
      )
