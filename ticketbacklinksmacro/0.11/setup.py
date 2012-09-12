#!/usr/bin/env python
# -*- coding: utf8 -*-

from setuptools import find_packages, setup

version='0.2'

setup(name='TicketBackLinksDescription',
      version=version,
      description="Add backlinks to ticket description",
      author='David Francos Cuartero (XayOn)',
      author_email='dfrancos@warp.es',
      keywords='trac plugin',
      license="GPLv3+",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      TicketBackLinksDescription.macro = TicketBackLinksDescription.macro
      """
      )
