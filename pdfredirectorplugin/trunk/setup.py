#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

version='0.2'

setup(name='PDFRedirector',
      version=version,
      description="Redirect PDF preview pages to the raw file",
      author='Nicholas Bergson-Shilcock',
      author_email='nicholasbs@openplans.org',
      url='http://nicholasbs.net',
      keywords='trac plugin',
      license="GPLv3",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'pdfredirector': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
          [trac.plugins]
          pdfredirector = pdfredirector
      """,
      )

