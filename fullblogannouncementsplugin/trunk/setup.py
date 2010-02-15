#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, Robert Corsaro
# All rights reserved.
#
# Distributed under the same licence as the latest Trac:
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.

from setuptools import find_packages, setup

setup(
      name='TracFullBlogAnnouncements',
      version='0.11',
      description="Announcements of blog post/comment changes",
      author='Robert Corsaro',
      author_email='doki_pen@doki-pen.org',
      url='http://github.com/dokipen/trac-fullblogannouncements-plugin',
      keywords='trac plugin',
      license="BSD",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      package_data = {
        'tracfullblogannouncements': 
          [
            'templates/*.html', 
            'templates/*.txt',
          ],
      },
      entry_points = {
        'trac.plugins': [
          'tracfullblogannouncements.producer = tracfullblogannouncements.producer',
          'tracfullblogannouncements.subscriber = tracfullblogannouncements.subscriber',
          'tracfullblogannouncements.formatter = tracfullblogannouncements.formatter',
        ],
      },
)
