#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'trac_unread'

setup(name=PACKAGE,
      description='Read/Unread comment tracker for Trac',
      keywords='last unread forum',
      version='0.0.1',
      author='Vladislav Naumov',
      author_email='vnaum@vnaum.com',
      packages=[PACKAGE],
      entry_points={'trac.plugins': 'trac_unread = trac_unread'}
      )


