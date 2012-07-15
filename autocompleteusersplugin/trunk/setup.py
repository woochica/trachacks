#/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Jeff Hammel
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

version='0.4.2'

setup(name='AutocompleteUsers',
      version=version,
      description="complete the known trac users, AJAX style",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      maintainer = 'Ryan J Ollos',
      maintainer_email = 'ryano@physiosonics.com',
      url='http://trac-hacks.org/wiki/AutocompleteUsersPlugin',
      keywords='trac plugin',
      license='3-Clause BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),      
      include_package_data=True,
      package_data={'autocompleteusers': ['htdocs/css/*.css', 'htdocs/css/*.gif', 'htdocs/js/*.js']},
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      autocompleteusers = autocompleteusers
      """,
      )

